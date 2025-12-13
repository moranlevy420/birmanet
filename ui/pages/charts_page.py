"""
Charts page - data visualizations.
"""

import streamlit as st
import pandas as pd

from config.settings import COLORS
from ui.components.charts import (
    create_bar_chart,
    create_scatter_chart,
    create_histogram,
    create_pie_chart,
    apply_chart_style
)
import plotly.express as px


def render_charts(df: pd.DataFrame) -> None:
    """Render the charts tab with various visualizations."""
    st.subheader("📊 Data Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 10 by Monthly Yield
        if 'MONTHLY_YIELD' in df.columns:
            top_yield = df.nlargest(10, 'MONTHLY_YIELD')
            fig1 = create_bar_chart(
                top_yield,
                x='MONTHLY_YIELD',
                y='FUND_NAME',
                orientation='h',
                title='🏆 Top 10 Funds by Monthly Yield',
                labels={'MONTHLY_YIELD': 'Monthly Yield (%)', 'FUND_NAME': ''},
                color='MONTHLY_YIELD',
                color_scale='Viridis',
                height=400
            )
            fig1.update_traces(hovertemplate='<b>%{y}</b><br>Yield: %{x:.2f}%<extra></extra>')
            st.plotly_chart(fig1, use_container_width=True, key="chart_top10_yield")
    
    with col2:
        # Top 10 by Total Assets
        if 'TOTAL_ASSETS' in df.columns:
            top_assets = df.nlargest(10, 'TOTAL_ASSETS')
            fig2 = create_bar_chart(
                top_assets,
                x='TOTAL_ASSETS',
                y='FUND_NAME',
                orientation='h',
                title='💰 Top 10 Funds by Total Assets',
                labels={'TOTAL_ASSETS': 'Total Assets (M)', 'FUND_NAME': ''},
                color='TOTAL_ASSETS',
                color_scale='Blues',
                height=400
            )
            fig2.update_traces(hovertemplate='<b>%{y}</b><br>Assets: %{x:,.0f}M<extra></extra>')
            st.plotly_chart(fig2, use_container_width=True, key="chart_top10_assets")
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Yield vs Fee scatter
        if 'AVG_ANNUAL_MANAGEMENT_FEE' in df.columns and 'MONTHLY_YIELD' in df.columns:
            scatter_df = df.dropna(subset=['AVG_ANNUAL_MANAGEMENT_FEE', 'MONTHLY_YIELD'])
            if len(scatter_df) > 0:
                fig3 = create_scatter_chart(
                    scatter_df,
                    x='AVG_ANNUAL_MANAGEMENT_FEE',
                    y='MONTHLY_YIELD',
                    size='TOTAL_ASSETS' if 'TOTAL_ASSETS' in df.columns else None,
                    color='FUND_CLASSIFICATION' if 'FUND_CLASSIFICATION' in df.columns else None,
                    hover_name='FUND_NAME',
                    title='📈 Monthly Yield vs Management Fee',
                    labels={
                        'AVG_ANNUAL_MANAGEMENT_FEE': 'Management Fee (%)',
                        'MONTHLY_YIELD': 'Monthly Yield (%)',
                        'FUND_CLASSIFICATION': 'Classification'
                    },
                    height=400
                )
                fig3.update_traces(hovertemplate='<b>%{hovertext}</b><br>Fee: %{x:.2f}%<br>Yield: %{y:.2f}%<extra></extra>')
                st.plotly_chart(fig3, use_container_width=True, key="chart_yield_vs_fee")
    
    with col4:
        # Distribution of yields
        if 'MONTHLY_YIELD' in df.columns:
            fig4 = create_histogram(
                df,
                x='MONTHLY_YIELD',
                nbins=30,
                title='📊 Distribution of Monthly Yields',
                labels={'MONTHLY_YIELD': 'Monthly Yield (%)', 'count': 'Number of Funds'},
                add_mean_line=True,
                height=400
            )
            st.plotly_chart(fig4, use_container_width=True, key="chart_yield_dist")
    
    # Classification breakdown
    if 'FUND_CLASSIFICATION' in df.columns:
        st.subheader("📁 By Classification")
        col5, col6 = st.columns(2)
        
        with col5:
            class_stats = df.groupby('FUND_CLASSIFICATION').agg({
                'FUND_ID': 'count',
                'TOTAL_ASSETS': 'sum',
                'MONTHLY_YIELD': 'mean'
            }).reset_index()
            class_stats.columns = ['Classification', 'Count', 'Total Assets', 'Avg Yield']
            
            fig5 = create_pie_chart(
                class_stats,
                values='Total Assets',
                names='Classification',
                title='💼 Total Assets by Classification',
                height=350
            )
            st.plotly_chart(fig5, use_container_width=True, key="chart_assets_by_class")
        
        with col6:
            fig6 = px.bar(
                class_stats,
                x='Classification',
                y='Avg Yield',
                title='📈 Average Yield by Classification',
                color='Classification',
                color_discrete_sequence=COLORS
            )
            fig6.update_traces(hovertemplate='<b>%{x}</b><br>Avg Yield: %{y:.2f}%<extra></extra>')
            fig6 = apply_chart_style(fig6, height=350, show_legend=False)
            st.plotly_chart(fig6, use_container_width=True, key="chart_yield_by_class")

