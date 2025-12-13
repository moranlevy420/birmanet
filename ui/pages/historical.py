"""
Historical Trends page - detailed fund history analysis.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config.settings import COLORS
from ui.components.tables import create_statistics_table


def render_historical(all_df: pd.DataFrame) -> None:
    """Render the historical trends tab."""
    st.subheader("📈 Historical Trends")
    
    # Fund selector
    fund_options = all_df[['FUND_ID', 'FUND_NAME']].drop_duplicates()
    fund_dict = dict(zip(fund_options['FUND_NAME'], fund_options['FUND_ID']))
    
    selected_fund = st.selectbox(
        "Select a fund to view history",
        options=list(fund_dict.keys()),
        key="historical_fund_select"
    )
    
    if not selected_fund:
        return
    
    fund_id = fund_dict[selected_fund]
    fund_history = all_df[all_df['FUND_ID'] == fund_id].sort_values('REPORT_DATE')
    
    if len(fund_history) == 0:
        st.warning("No historical data available for this fund")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    latest = fund_history.iloc[-1]
    
    with col1:
        st.metric("Total Data Points", len(fund_history))
    
    with col2:
        date_range = f"{fund_history['REPORT_DATE'].min().strftime('%Y-%m')} to {fund_history['REPORT_DATE'].max().strftime('%Y-%m')}"
        st.metric("Date Range", date_range)
    
    with col3:
        avg_yield = fund_history['MONTHLY_YIELD'].mean()
        st.metric("Avg Monthly Yield", f"{avg_yield:.2f}%")
    
    with col4:
        if len(fund_history) > 1 and 'TOTAL_ASSETS' in fund_history.columns:
            first_assets = fund_history.iloc[0]['TOTAL_ASSETS']
            if first_assets > 0:
                asset_growth = ((latest['TOTAL_ASSETS'] - first_assets) / first_assets * 100)
                st.metric("Asset Growth", f"{asset_growth:.1f}%")
            else:
                st.metric("Asset Growth", "N/A")
        else:
            st.metric("Asset Growth", "N/A")
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Monthly Yield', 'Total Assets', 'Year-to-Date Yield', 'Management Fee'),
        vertical_spacing=0.18,
        horizontal_spacing=0.10
    )
    
    # Monthly Yield
    fig.add_trace(
        go.Scatter(
            x=fund_history['REPORT_DATE'],
            y=fund_history['MONTHLY_YIELD'],
            mode='lines+markers',
            name='Monthly Yield',
            line=dict(color=COLORS[0]),
            hovertemplate='%{x|%Y/%m}: %{y:.2f}%<extra></extra>'
        ),
        row=1, col=1
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    
    # Total Assets
    if 'TOTAL_ASSETS' in fund_history.columns:
        fig.add_trace(
            go.Scatter(
                x=fund_history['REPORT_DATE'],
                y=fund_history['TOTAL_ASSETS'],
                mode='lines+markers',
                name='Total Assets',
                line=dict(color=COLORS[1]),
                fill='tozeroy',
                fillcolor='rgba(124, 58, 237, 0.1)',
                hovertemplate='%{x|%Y/%m}: %{y:,.0f}M<extra></extra>'
            ),
            row=1, col=2
        )
    
    # YTD Yield
    if 'YEAR_TO_DATE_YIELD' in fund_history.columns:
        fig.add_trace(
            go.Scatter(
                x=fund_history['REPORT_DATE'],
                y=fund_history['YEAR_TO_DATE_YIELD'],
                mode='lines+markers',
                name='YTD Yield',
                line=dict(color=COLORS[2]),
                hovertemplate='%{x|%Y/%m}: %{y:.2f}%<extra></extra>'
            ),
            row=2, col=1
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
    
    # Management Fee
    if 'AVG_ANNUAL_MANAGEMENT_FEE' in fund_history.columns:
        fig.add_trace(
            go.Scatter(
                x=fund_history['REPORT_DATE'],
                y=fund_history['AVG_ANNUAL_MANAGEMENT_FEE'],
                mode='lines+markers',
                name='Mgmt Fee',
                line=dict(color=COLORS[3]),
                hovertemplate='%{x|%Y/%m}: %{y:.2f}%<extra></extra>'
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        height=700,
        showlegend=False,
        title_text=f"📊 {selected_fund}",
        hovermode='closest'
    )
    
    fig.update_xaxes(
        tickformat='%Y/%m',
        tickangle=-45,
        showgrid=True,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor='rgba(128,128,128,0.3)',
        zeroline=True,
        zerolinecolor='rgba(128,128,128,0.5)'
    )
    
    st.plotly_chart(fig, use_container_width=True, key="historical_trends_chart")
    
    # Statistics table
    st.markdown("### 📊 Statistics Summary")
    stats_table = create_statistics_table(fund_history)
    st.dataframe(stats_table, use_container_width=True, hide_index=True, key="historical_stats_table")

