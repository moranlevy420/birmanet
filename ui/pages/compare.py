"""
Compare Funds page - side-by-side fund comparison.
"""

import streamlit as st
import pandas as pd

from config.settings import COLORS
from ui.components.tables import create_comparison_table
from ui.components.charts import apply_chart_style
import plotly.express as px


def render_comparison(df: pd.DataFrame, all_df: pd.DataFrame) -> None:
    """Render the fund comparison tab."""
    st.subheader("⚖️ Compare Funds")
    
    # Get unique funds
    fund_options = df[['FUND_ID', 'FUND_NAME']].drop_duplicates()
    fund_dict = dict(zip(fund_options['FUND_NAME'], fund_options['FUND_ID']))
    
    # Select funds to compare
    default_funds = list(fund_dict.keys())[:2] if len(fund_dict) >= 2 else list(fund_dict.keys())
    selected_funds = st.multiselect(
        "Select funds to compare (up to 5)",
        options=list(fund_dict.keys()),
        max_selections=5,
        default=default_funds
    )
    
    if len(selected_funds) < 2:
        st.warning("Please select at least 2 funds to compare")
        return
    
    selected_fund_ids = [fund_dict[name] for name in selected_funds]
    
    # Comparison table
    st.markdown("### 📋 Side-by-Side Comparison")
    comparison_table = create_comparison_table(df, selected_funds, fund_dict)
    st.dataframe(comparison_table, use_container_width=True, hide_index=True)
    
    # Historical comparison chart
    st.markdown("### 📈 Historical Performance")
    
    historical_df = all_df[all_df['FUND_ID'].isin(selected_fund_ids)].copy()
    
    if len(historical_df) > 0:
        # Create short names for hover
        unique_funds = [f for f in historical_df['FUND_NAME'].unique().tolist() if isinstance(f, str)]
        short_name_map = {name: name.split()[0] if len(name.split()) > 0 else name[:15] for name in unique_funds}
        historical_df['SHORT_NAME'] = historical_df['FUND_NAME'].map(short_name_map)
        
        # Monthly Yield chart
        fig = px.line(
            historical_df.sort_values(['FUND_NAME', 'REPORT_DATE']),
            x='REPORT_DATE',
            y='MONTHLY_YIELD',
            color='FUND_NAME',
            custom_data=['SHORT_NAME'],
            title='Monthly Yield Over Time',
            labels={'REPORT_DATE': 'Date', 'MONTHLY_YIELD': 'Monthly Yield (%)', 'FUND_NAME': 'Fund'},
            color_discrete_sequence=COLORS
        )
        fig.update_traces(
            mode='lines+markers',
            hovertemplate='<b>%{customdata[0]}</b><br>%{x|%Y/%m}: %{y:.2f}%<extra></extra>'
        )
        fig = apply_chart_style(fig, height=400, is_time_series=True, historical_df=historical_df)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        st.plotly_chart(fig, use_container_width=True)
        
        # Assets over time
        if 'TOTAL_ASSETS' in historical_df.columns:
            fig2 = px.line(
                historical_df.sort_values(['FUND_NAME', 'REPORT_DATE']),
                x='REPORT_DATE',
                y='TOTAL_ASSETS',
                color='FUND_NAME',
                custom_data=['SHORT_NAME'],
                title='Total Assets Over Time',
                labels={'REPORT_DATE': 'Date', 'TOTAL_ASSETS': 'Total Assets (M)', 'FUND_NAME': 'Fund'},
                color_discrete_sequence=COLORS
            )
            fig2.update_traces(
                mode='lines+markers',
                hovertemplate='<b>%{customdata[0]}</b><br>%{x|%Y/%m}: %{y:,.0f}M<extra></extra>'
            )
            fig2 = apply_chart_style(fig2, height=400, is_time_series=True, historical_df=historical_df)
            st.plotly_chart(fig2, use_container_width=True)

