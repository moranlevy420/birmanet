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
import plotly.graph_objects as go


def render_world_view(
    filtered_df: pd.DataFrame,
    all_df: pd.DataFrame,
    selected_period: int,
    dataset_name: str
) -> None:
    """Render the World View tab with data table and top 5 chart."""
    
    # Initialize session state for sort (only once)
    if 'sort_column' not in st.session_state:
        st.session_state.sort_column = '1Y (%)'
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = 'Descending'
    if 'detected_sort_column' not in st.session_state:
        st.session_state.detected_sort_column = '1Y (%)'
    
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
    
    # Filter hash for table key
    filter_hash = f"{selected_period}_{len(filtered_df)}"
    
    # Get current sort column from session state (persists across filter changes)
    current_sort_column = st.session_state.get('detected_sort_column', '1Y (%)')
    
    # Render data table with persistent sort
    sorted_df, grid_response = create_fund_table(
        filtered_df,
        height=280,
        key="world_view_table",
        filter_hash=filter_hash,
        sort_column=current_sort_column,
        sort_ascending=False
    )
    
    # Try to get sort column from AgGrid column state first (most reliable)
    detected_sort = None
    
    # Check if grid_response has columns_state with sort info (dict or object)
    col_state = None
    if isinstance(grid_response, dict):
        col_state = grid_response.get('columns_state') or grid_response.get('column_state')
    elif hasattr(grid_response, 'columns_state'):
        col_state = grid_response.columns_state
    elif hasattr(grid_response, 'column_state'):
        col_state = grid_response.column_state
    
    if col_state:
        for cs in col_state:
            sort_dir = cs.get('sort') if isinstance(cs, dict) else getattr(cs, 'sort', None)
            if sort_dir:
                col_id = cs.get('colId') if isinstance(cs, dict) else getattr(cs, 'colId', None)
                if col_id:
                    detected_sort = col_id
                    break
    
    # Fallback: detect by comparing data order using Fund ID (more unique)
    if not detected_sort and len(sorted_df) > 0:
        id_col = 'Fund ID' if 'Fund ID' in sorted_df.columns else 'Fund Name'
        current_order = list(sorted_df.head(30)[id_col])
        
        # All sortable columns - check all of them
        sortable_cols = [
            'Sub-Product', 'Inception', 'Mgmt (%)', 'Deposit (%)',
            'Liquid (%)', 'Currency (%)', 'Foreign (%)', 'Stocks (%)', 'Σ Assets (M)',
            '1M (%)', 'YTD (%)', '1Y (%)', '3Y (%)', '5Y (%)', 'Sharpe', 'Std Dev',
            'Alpha', 'Net Deposits', 'Fund ID', 'Fund Name',
        ]
        for col in sortable_cols:
            if col in sorted_df.columns and sorted_df[col].notna().sum() > 0:
                try:
                    # Try descending
                    col_sorted_desc = sorted_df.sort_values(col, ascending=False, na_position='last')
                    if list(col_sorted_desc.head(30)[id_col]) == current_order:
                        detected_sort = col
                        break
                    # Try ascending
                    col_sorted_asc = sorted_df.sort_values(col, ascending=True, na_position='last')
                    if list(col_sorted_asc.head(30)[id_col]) == current_order:
                        detected_sort = col
                        break
                except:
                    continue
    
    # Update session state if we detected a different sort, and rerun to update title
    if detected_sort:
        if detected_sort != st.session_state.get('detected_sort_column'):
            st.session_state.detected_sort_column = detected_sort
            st.rerun()
        sort_column = detected_sort
    else:
        sort_column = st.session_state.get('detected_sort_column', '1Y (%)')
    
    # Don't use cumulative - show raw values from table to match
    show_cumulative = False
    
    # Main title above both charts with range selector
    col_main_title, col_range = st.columns([4, 1])
    with col_main_title:
        cumulative_note = " *(cumulative)*" if show_cumulative else ""
        st.markdown(f"**🏆 Top 5 by {sort_column}**{cumulative_note}")
    with col_range:
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
        # Show raw values from data (matching table)
        show_cumulative = False
        
        # Create short names for hover
        unique_funds = [f for f in historical_df['FUND_NAME'].unique().tolist() if isinstance(f, str)]
        short_name_map = {name: get_short_unique_name(name, unique_funds) for name in unique_funds}
        historical_df['SHORT_NAME'] = historical_df['FUND_NAME'].map(short_name_map)
        
        if show_cumulative and 'MONTHLY_YIELD' in historical_df.columns:
            # Calculate cumulative compounded returns for each fund
            chart_data = []
            for fund_name in top5_fund_names:
                fund_df = historical_df[historical_df['FUND_NAME'] == fund_name].sort_values('REPORT_DATE')
                if len(fund_df) > 0:
                    # Calculate cumulative compounded return
                    # (1 + r1/100) * (1 + r2/100) * ... - 1
                    fund_df = fund_df.copy()
                    growth_factors = 1 + (fund_df['MONTHLY_YIELD'] / 100)
                    cumulative = growth_factors.cumprod()
                    fund_df['CUMULATIVE_RETURN'] = (cumulative - 1) * 100
                    chart_data.append(fund_df)
            
            if chart_data:
                chart_df = pd.concat(chart_data, ignore_index=True)
                chart_col = 'CUMULATIVE_RETURN'
                chart_label = 'Cumulative Return (%)'
            else:
                chart_df = historical_df
                chart_col = 'MONTHLY_YIELD'
                chart_label = 'Monthly Yield (%)'
        else:
            # Show regular monthly yields
            chart_df = historical_df
            reverse_labels = {v: k for k, v in COLUMN_LABELS.items()}
            original_col = reverse_labels.get(sort_column, 'MONTHLY_YIELD')
            
            if original_col in chart_df.columns and chart_df[original_col].notna().any():
                chart_col = original_col
                chart_label = sort_column
            else:
                chart_col = 'MONTHLY_YIELD'
                chart_label = 'Monthly Yield (%)'
        
        # Create two columns for charts with minimal gap
        chart_col1, chart_col2 = st.columns([3, 2], gap="small")
        
        with chart_col1:
            # Title for fund performance chart
            st.markdown("**📈 Performance**")
            
            # Create line chart for yield/returns over time
            fig = px.line(
                chart_df.sort_values(['FUND_NAME', 'REPORT_DATE']),
                x='REPORT_DATE',
                y=chart_col,
                color='FUND_NAME',
                custom_data=['SHORT_NAME'],
                labels={
                    'REPORT_DATE': 'Date',
                    chart_col: chart_label,
                    'FUND_NAME': ''
                },
                color_discrete_sequence=COLORS,
                category_orders={'FUND_NAME': top5_fund_names}
            )
            
            fig.update_traces(
                mode='lines+markers',
                hovertemplate='<b>%{customdata[0]}</b><br>%{x|%b %Y}: %{y:.2f}%<extra></extra>'
            )
            
            # Move legend above the chart, compact margins, show all months on x-axis
            all_dates = chart_df['REPORT_DATE'].unique()
            fig.update_layout(
                height=300,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=10)
                ),
                margin=dict(l=40, r=10, t=60, b=50),
                xaxis=dict(
                    tickformat='%b %Y',
                    tickmode='array',
                    tickvals=all_dates,
                    tickangle=-45,
                    tickfont=dict(size=9)
                )
            )
            
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            st.plotly_chart(fig, use_container_width=True, key="world_view_top5_chart")
        
        with chart_col2:
            # Title for exposure chart
            st.markdown("**📊 Exposures**")
            
            # Get exposure data for top 5 funds
            exposure_data = []
            fund_short_names = []
            for fund_name in top5_fund_names:
                fund_data = filtered_df[filtered_df['FUND_NAME'] == fund_name]
                if len(fund_data) > 0:
                    fund = fund_data.iloc[0]
                    short_name = short_name_map.get(fund_name, fund_name[:15])
                    fund_short_names.append(short_name)
                    exposure_data.append({
                        'Fund': short_name,
                        'Stocks': fund.get('STOCK_MARKET_EXPOSURE', 0) or 0,
                        'Foreign': fund.get('FOREIGN_EXPOSURE', 0) or 0,
                        'Currency': fund.get('FOREIGN_CURRENCY_EXPOSURE', 0) or 0,
                        'Liquid': fund.get('LIQUID_ASSETS_PERCENT', 0) or 0
                    })
            
            if exposure_data:
                exp_df = pd.DataFrame(exposure_data)
                
                # Create grouped bar chart - group by exposure type, bars for each fund
                # Use same colors as line chart (COLORS) for fund correlation
                exp_fig = go.Figure()
                
                exposure_types = ['Stocks', 'Foreign', 'Currency', 'Liquid']
                
                # Add a bar trace for each fund (same color as line chart)
                for i, row in exp_df.iterrows():
                    fund_name = row['Fund']
                    fund_values = [row[exp] for exp in exposure_types]
                    exp_fig.add_trace(go.Bar(
                        name=fund_name,
                        x=exposure_types,
                        y=fund_values,
                        marker_color=COLORS[i % len(COLORS)],
                        hovertemplate=f'<b>{fund_name}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>'
                    ))
                
                exp_fig.update_layout(
                    barmode='group',
                    height=280,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=9)
                    ),
                    margin=dict(l=10, r=10, t=50, b=40),
                    xaxis_title="",
                    yaxis_title="%",
                    xaxis_tickfont=dict(size=10)
                )
                
                st.plotly_chart(exp_fig, use_container_width=True, key="world_view_exposure_chart")
            else:
                st.info("No exposure data available")
    else:
        st.info("No historical data available for the selected funds.")

