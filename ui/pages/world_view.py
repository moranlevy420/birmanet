"""
World View page - main data table with top 5 chart.
"""

import streamlit as st
import pandas as pd
from typing import Optional

from config.settings import COLUMN_LABELS, COLORS
from ui.components.tables import create_fund_table
from ui.components.charts import create_line_chart, apply_chart_style
from utils.formatters import format_period, get_short_unique_name
import plotly.express as px


def render_world_view(
    filtered_df: pd.DataFrame,
    all_df: pd.DataFrame,
    selected_period: int,
    dataset_name: str
) -> None:
    """Render the World View tab with data table and top 5 chart."""
    
    # Initialize session state for sort
    if 'sort_column' not in st.session_state:
        st.session_state.sort_column = 'YTD Yield (%)'
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = 'Descending'
    if 'grid_initialized' not in st.session_state:
        st.session_state.grid_initialized = True
        st.rerun()
    
    # Title and Download button
    col_title, col_download = st.columns([4, 1])
    with col_title:
        st.subheader(f"📋 {dataset_name} - {format_period(selected_period)}")
    with col_download:
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV",
            data=csv,
            file_name=f"funds_{selected_period}.csv",
            mime="text/csv",
            key="download_csv_btn"
        )
    
    # Render data table
    sorted_df, grid_response = create_fund_table(
        filtered_df,
        height=280,
        key="world_view_table"
    )
    
    # Detect which column is sorted by comparing with what each column's sort would produce
    detected_sort = None
    if len(sorted_df) > 0 and 'Fund Name' in sorted_df.columns:
        current_order = list(sorted_df.head(5)['Fund Name'])
        numeric_cols = ['Monthly Yield (%)', 'YTD Yield (%)', '3Y Avg Yield (%)', 
                      '5Y Avg Yield (%)', 'Sharpe Ratio', 'Total Assets (M)',
                      'Std Dev', 'Stock Exposure (%)', 'Foreign Exposure (%)']
        for col in numeric_cols:
            if col in sorted_df.columns:
                # Try descending
                col_sorted_desc = sorted_df.sort_values(col, ascending=False, na_position='last')
                if list(col_sorted_desc.head(5)['Fund Name']) == current_order:
                    detected_sort = col
                    break
                # Try ascending
                col_sorted_asc = sorted_df.sort_values(col, ascending=True, na_position='last')
                if list(col_sorted_asc.head(5)['Fund Name']) == current_order:
                    detected_sort = col
                    break
    
    # Update session state if we detected a different sort, and rerun to update title
    if detected_sort:
        if detected_sort != st.session_state.get('detected_sort_column'):
            st.session_state.detected_sort_column = detected_sort
            st.rerun()
        sort_column = detected_sort
    else:
        sort_column = st.session_state.get('detected_sort_column', 'YTD Yield (%)')
    col_chart_title, col_chart_range = st.columns([3, 1])
    with col_chart_title:
        st.markdown(f"**📈 Top 5 by {sort_column}**")
    with col_chart_range:
        months_range = st.selectbox(
            "Range",
            options=[12, 24, 36, 0],
            format_func=lambda x: f"{x}M" if x > 0 else "All",
            index=0,
            label_visibility="collapsed",
            key="chart_months_range"
        )
    
    # Get top 5 funds from sorted table
    top5_display = sorted_df.head(5)
    top5_fund_names = top5_display['Fund Name'].tolist()
    
    # Get fund IDs
    fund_name_to_id = filtered_df.set_index('FUND_NAME')['FUND_ID'].to_dict()
    top5_fund_ids = [fund_name_to_id.get(name) for name in top5_fund_names if name in fund_name_to_id]
    
    # Get historical data
    historical_df = all_df[all_df['FUND_ID'].isin(top5_fund_ids)].copy()
    
    # Set FUND_NAME as categorical with order matching table
    historical_df['FUND_NAME'] = pd.Categorical(
        historical_df['FUND_NAME'],
        categories=top5_fund_names,
        ordered=True
    )
    
    # Filter to show data up to selected period
    selected_date = pd.to_datetime(str(selected_period), format='%Y%m')
    historical_df = historical_df[historical_df['REPORT_DATE'] <= selected_date]
    
    # Filter by time range
    if months_range > 0 and len(historical_df) > 0:
        min_date = selected_date - pd.DateOffset(months=months_range)
        historical_df = historical_df[historical_df['REPORT_DATE'] >= min_date]
    
    if len(historical_df) > 0:
        # Find original column for sort
        reverse_labels = {v: k for k, v in COLUMN_LABELS.items()}
        original_col = reverse_labels.get(sort_column, 'MONTHLY_YIELD')
        
        if original_col in historical_df.columns and historical_df[original_col].notna().any():
            chart_col = original_col
            chart_label = sort_column
        else:
            chart_col = 'MONTHLY_YIELD'
            chart_label = 'Monthly Yield (%)'
        
        # Create short names for hover
        unique_funds = [f for f in historical_df['FUND_NAME'].unique().tolist() if isinstance(f, str)]
        short_name_map = {name: get_short_unique_name(name, unique_funds) for name in unique_funds}
        historical_df['SHORT_NAME'] = historical_df['FUND_NAME'].map(short_name_map)
        
        # Create chart
        fig = px.line(
            historical_df.sort_values(['FUND_NAME', 'REPORT_DATE']),
            x='REPORT_DATE',
            y=chart_col,
            color='FUND_NAME',
            custom_data=['SHORT_NAME'],
            labels={
                'REPORT_DATE': 'Date',
                chart_col: chart_label,
                'FUND_NAME': 'Fund'
            },
            color_discrete_sequence=COLORS,
            category_orders={'FUND_NAME': top5_fund_names}
        )
        
        fig.update_traces(
            mode='lines+markers',
            hovertemplate='<b>%{customdata[0]}</b><br>%{x|%Y/%m}: %{y:.2f}%<extra></extra>'
        )
        
        fig = apply_chart_style(fig, height=320, is_time_series=True, historical_df=historical_df)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Include fund IDs in key so chart updates when sort order changes
        fund_ids_str = '-'.join(str(fid) for fid in top5_fund_ids if fid is not None)
        chart_key = f"top5_chart_{selected_period}_{sort_column}_{months_range}_{fund_ids_str}"
        st.plotly_chart(fig, use_container_width=True, key=chart_key)
    else:
        st.info("No historical data available for the selected funds.")

