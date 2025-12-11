"""
Pension Funds Explorer - Interactive Dashboard
Fetches and displays pension fund data from data.gov.il

Run with: streamlit run pensia_app.py
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Pension Funds Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1e3a5f 0%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
RESOURCE_IDS = [
    "6d47d6b5-cb08-488b-b333-f1e717b1e1bd",  # 2024-2025 data
    "4694d5a7-5284-4f3d-a2cb-5887f43fb55e",  # 2023 data
]
BASE_URL = "https://data.gov.il/api/3/action/datastore_search"

# Columns to display
DISPLAY_COLUMNS = [
    'FUND_ID',
    'FUND_NAME',
    'REPORT_PERIOD',
    'FUND_CLASSIFICATION',
    'TOTAL_ASSETS',
    'AVG_ANNUAL_MANAGEMENT_FEE',
    'AVG_DEPOSIT_FEE',
    'MONTHLY_YIELD',
    'YEAR_TO_DATE_YIELD',
    'AVG_ANNUAL_YIELD_TRAILING_3YRS',
    'AVG_ANNUAL_YIELD_TRAILING_5YRS',
    'STANDARD_DEVIATION',
    'SHARPE_RATIO',
    'LIQUID_ASSETS_PERCENT',
    'STOCK_MARKET_EXPOSURE',
    'FOREIGN_EXPOSURE',
    'FOREIGN_CURRENCY_EXPOSURE',
    'CURRENT_DATE',
]

# Column display names
COLUMN_LABELS = {
    'FUND_ID': 'Fund ID',
    'FUND_NAME': 'Fund Name',
    'REPORT_PERIOD': 'Report Period',
    'FUND_CLASSIFICATION': 'Classification',
    'TOTAL_ASSETS': 'Total Assets (M)',
    'AVG_ANNUAL_MANAGEMENT_FEE': 'Mgmt Fee (%)',
    'AVG_DEPOSIT_FEE': 'Deposit Fee (%)',
    'MONTHLY_YIELD': 'Monthly Yield (%)',
    'YEAR_TO_DATE_YIELD': 'YTD Yield (%)',
    'AVG_ANNUAL_YIELD_TRAILING_3YRS': '3Y Avg Yield (%)',
    'AVG_ANNUAL_YIELD_TRAILING_5YRS': '5Y Avg Yield (%)',
    'STANDARD_DEVIATION': 'Std Dev',
    'SHARPE_RATIO': 'Sharpe Ratio',
    'LIQUID_ASSETS_PERCENT': 'Liquid Assets (%)',
    'STOCK_MARKET_EXPOSURE': 'Stock Exposure (%)',
    'FOREIGN_EXPOSURE': 'Foreign Exposure (%)',
    'FOREIGN_CURRENCY_EXPOSURE': 'Currency Exposure (%)',
    'CURRENT_DATE': 'Data Date',
}

# Color palette
COLORS = ['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0891b2', '#be185d', '#4f46e5', '#065f46', '#9333ea']


@st.cache_data(ttl=3600)
def fetch_all_data():
    """Fetch all pension fund data from multiple API resources."""
    all_records = []
    
    for resource_id in RESOURCE_IDS:
        offset = 0
        batch_size = 32000
        
        while True:
            params = {
                "resource_id": resource_id,
                "limit": batch_size,
                "offset": offset
            }
            response = requests.get(BASE_URL, params=params)
            data = response.json()
            
            if not data.get("success"):
                st.warning(f"API Error for resource {resource_id}: {data.get('error')}")
                break
            
            records = data["result"]["records"]
            all_records.extend(records)
            total = data["result"]["total"]
            
            if offset + batch_size >= total:
                break
            offset += batch_size
    
    df = pd.DataFrame(all_records)
    
    # Remove duplicates (same FUND_ID and REPORT_PERIOD)
    df = df.drop_duplicates(subset=['FUND_ID', 'REPORT_PERIOD'], keep='first')
    
    # Create date column for plotting
    df['REPORT_DATE'] = pd.to_datetime(df['REPORT_PERIOD'].astype(str), format='%Y%m')
    
    # Check if exposure values need conversion (if max > 100, they're absolute values)
    exposure_cols = ['STOCK_MARKET_EXPOSURE', 'FOREIGN_EXPOSURE', 'FOREIGN_CURRENCY_EXPOSURE']
    for col in exposure_cols:
        if col in df.columns:
            # Only convert if values appear to be absolute (max > 100)
            if df[col].max() > 100:
                df[col] = (df[col] / df['TOTAL_ASSETS'] * 100).round(2)
    
    return df


def format_period(period: int) -> str:
    """Format period number to readable string."""
    year = period // 100
    month = period % 100
    months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    return f"{months[month]} {year}"


def render_data_table(df, selected_period, all_df):
    """Render the main data table tab."""
    # Initialize session state for sort if not exists
    if 'sort_column' not in st.session_state:
        st.session_state.sort_column = 'YTD Yield (%)'
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = 'Descending'
    
    # Sort controls (compact row)
    col_sort1, col_sort2, col_sort3 = st.columns([2, 1, 1])
    with col_sort1:
        sort_column = st.selectbox(
            "Sort by",
            options=list(COLUMN_LABELS.values()),
            index=list(COLUMN_LABELS.values()).index(st.session_state.sort_column),
            label_visibility="collapsed"
        )
        st.session_state.sort_column = sort_column
    with col_sort2:
        sort_order = st.radio(
            "Order", 
            ["↓ Desc", "↑ Asc"], 
            horizontal=True,
            index=0 if st.session_state.sort_order == "Descending" else 1,
            label_visibility="collapsed"
        )
        st.session_state.sort_order = "Descending" if sort_order == "↓ Desc" else "Ascending"
    
    # Prepare display dataframe
    display_df = df[DISPLAY_COLUMNS].copy()
    display_df = display_df.rename(columns=COLUMN_LABELS)
    
    ascending = sort_order == "↑ Asc"
    display_df = display_df.sort_values(by=sort_column, ascending=ascending, na_position='last')
    display_df = display_df.reset_index(drop=True)
    
    # Add row number as first column
    display_df.insert(0, '#', range(1, len(display_df) + 1))
    
    # Download button in the third column
    with col_sort3:
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV",
            data=csv,
            file_name=f"pension_funds_{selected_period}.csv",
            mime="text/csv",
            key="download_csv_btn"
        )
    
    # Display table (compact height)
    st.dataframe(
        display_df,
        use_container_width=True,
        height=280,
        hide_index=True,
        column_config={
            "#": st.column_config.NumberColumn(format="%d", width="small"),
            "Fund ID": st.column_config.NumberColumn(format="%d"),
            "Fund Name": st.column_config.TextColumn(width="large"),
            "Report Period": st.column_config.NumberColumn(format="%d"),
            "Total Assets (M)": st.column_config.NumberColumn(format="%.2f"),
            "Mgmt Fee (%)": st.column_config.NumberColumn(format="%.2f"),
            "Deposit Fee (%)": st.column_config.NumberColumn(format="%.2f"),
            "Monthly Yield (%)": st.column_config.NumberColumn(format="%.2f"),
            "YTD Yield (%)": st.column_config.NumberColumn(format="%.2f"),
            "3Y Avg Yield (%)": st.column_config.NumberColumn(format="%.2f"),
            "5Y Avg Yield (%)": st.column_config.NumberColumn(format="%.2f"),
            "Std Dev": st.column_config.NumberColumn(format="%.2f"),
            "Sharpe Ratio": st.column_config.NumberColumn(format="%.2f"),
            "Liquid Assets (%)": st.column_config.NumberColumn(format="%.1f"),
            "Stock Exposure (%)": st.column_config.NumberColumn(format="%.2f"),
            "Foreign Exposure (%)": st.column_config.NumberColumn(format="%.2f"),
            "Currency Exposure (%)": st.column_config.NumberColumn(format="%.2f"),
        }
    )
    
    # Line chart for top 5 funds based on sort column
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
    
    # Get top 5 fund IDs from the sorted table (excluding the # column)
    top5_display = display_df.head(5)
    top5_fund_names = top5_display['Fund Name'].tolist()
    top5_fund_ids = df[df['FUND_NAME'].isin(top5_fund_names)]['FUND_ID'].unique()
    
    # Get historical data for these funds
    historical_df = all_df[all_df['FUND_ID'].isin(top5_fund_ids)].copy()
    
    # Filter to show data up to the selected report period
    selected_date = pd.to_datetime(str(selected_period), format='%Y%m')
    historical_df = historical_df[historical_df['REPORT_DATE'] <= selected_date]
    
    # Filter by time range (months back from selected period)
    if months_range > 0 and len(historical_df) > 0:
        min_date = selected_date - pd.DateOffset(months=months_range)
        historical_df = historical_df[historical_df['REPORT_DATE'] >= min_date]
    
    if len(historical_df) > 0:
        # Find the original column name for the sort column
        reverse_labels = {v: k for k, v in COLUMN_LABELS.items()}
        original_col = reverse_labels.get(sort_column, 'MONTHLY_YIELD')
        
        # Check if the column has data for time series
        if original_col in historical_df.columns and historical_df[original_col].notna().any():
            chart_col = original_col
            chart_label = sort_column
        else:
            # Fallback to MONTHLY_YIELD if the selected column has no data
            chart_col = 'MONTHLY_YIELD'
            chart_label = 'Monthly Yield (%)'
        
        # Dynamic chart showing the sorted column over time
        fig = px.line(
            historical_df.sort_values('REPORT_DATE'),
            x='REPORT_DATE',
            y=chart_col,
            color='FUND_NAME',
            labels={
                'REPORT_DATE': 'Date',
                chart_col: chart_label,
                'FUND_NAME': 'Fund'
            },
            color_discrete_sequence=COLORS
        )
        # Update hover template to show proper date
        fig.update_traces(
            mode='lines+markers',
            hovertemplate='%{x|%b %Y}<br>%{y:.2f}%<extra></extra>'
        )
        fig.update_layout(
            height=280,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                font=dict(size=10)
            ),
            margin=dict(t=10, b=50, l=50, r=150),
            xaxis=dict(
                tickformat='%Y-%m',
                tickmode='auto',
                nticks=10,
                tickangle=-45
            ),
            hovermode='closest'
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        # Key includes all factors that affect the chart
        chart_key = f"top5_chart_{selected_period}_{sort_column}_{sort_order}_{months_range}_{'-'.join(map(str, top5_fund_ids))}"
        st.plotly_chart(fig, use_container_width=True, key=chart_key)
    else:
        st.info("No historical data available for the selected funds.")


def render_charts(df):
    """Render the charts tab."""
    st.subheader("📊 Data Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 10 by Monthly Yield
        top_yield = df.nlargest(10, 'MONTHLY_YIELD')
        fig1 = px.bar(
            top_yield,
            x='MONTHLY_YIELD',
            y='FUND_NAME',
            orientation='h',
            title='🏆 Top 10 Funds by Monthly Yield',
            labels={'MONTHLY_YIELD': 'Monthly Yield (%)', 'FUND_NAME': ''},
            color='MONTHLY_YIELD',
            color_continuous_scale='Viridis'
        )
        fig1.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Top 10 by Total Assets
        top_assets = df.nlargest(10, 'TOTAL_ASSETS')
        fig2 = px.bar(
            top_assets,
            x='TOTAL_ASSETS',
            y='FUND_NAME',
            orientation='h',
            title='💰 Top 10 Funds by Total Assets',
            labels={'TOTAL_ASSETS': 'Total Assets (M)', 'FUND_NAME': ''},
            color='TOTAL_ASSETS',
            color_continuous_scale='Blues'
        )
        fig2.update_layout(height=400, showlegend=False, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Yield vs Fee scatter
        fig3 = px.scatter(
            df.dropna(subset=['AVG_ANNUAL_MANAGEMENT_FEE', 'MONTHLY_YIELD']),
            x='AVG_ANNUAL_MANAGEMENT_FEE',
            y='MONTHLY_YIELD',
            size='TOTAL_ASSETS',
            color='FUND_CLASSIFICATION',
            hover_name='FUND_NAME',
            title='📈 Monthly Yield vs Management Fee',
            labels={
                'AVG_ANNUAL_MANAGEMENT_FEE': 'Management Fee (%)',
                'MONTHLY_YIELD': 'Monthly Yield (%)',
                'FUND_CLASSIFICATION': 'Classification'
            }
        )
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        # Distribution of yields
        fig4 = px.histogram(
            df,
            x='MONTHLY_YIELD',
            nbins=30,
            title='📊 Distribution of Monthly Yields',
            labels={'MONTHLY_YIELD': 'Monthly Yield (%)', 'count': 'Number of Funds'},
            color_discrete_sequence=['#2563eb']
        )
        fig4.add_vline(x=df['MONTHLY_YIELD'].mean(), line_dash="dash", line_color="red",
                       annotation_text=f"Mean: {df['MONTHLY_YIELD'].mean():.2f}%")
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)
    
    # Classification breakdown
    st.subheader("📁 By Classification")
    col5, col6 = st.columns(2)
    
    with col5:
        class_stats = df.groupby('FUND_CLASSIFICATION').agg({
            'FUND_ID': 'count',
            'TOTAL_ASSETS': 'sum',
            'MONTHLY_YIELD': 'mean'
        }).reset_index()
        class_stats.columns = ['Classification', 'Count', 'Total Assets', 'Avg Yield']
        
        fig5 = px.pie(
            class_stats,
            values='Total Assets',
            names='Classification',
            title='💼 Total Assets by Classification',
            color_discrete_sequence=COLORS
        )
        fig5.update_layout(height=350)
        st.plotly_chart(fig5, use_container_width=True)
    
    with col6:
        fig6 = px.bar(
            class_stats,
            x='Classification',
            y='Avg Yield',
            title='📈 Average Yield by Classification',
            color='Classification',
            color_discrete_sequence=COLORS
        )
        fig6.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig6, use_container_width=True)


def render_comparison(df, all_df):
    """Render the fund comparison tab."""
    st.subheader("⚖️ Compare Funds")
    
    # Get unique funds
    fund_options = df[['FUND_ID', 'FUND_NAME']].drop_duplicates()
    fund_dict = dict(zip(fund_options['FUND_NAME'], fund_options['FUND_ID']))
    
    # Select funds to compare
    selected_funds = st.multiselect(
        "Select funds to compare (up to 5)",
        options=list(fund_dict.keys()),
        max_selections=5,
        default=list(fund_dict.keys())[:2] if len(fund_dict) >= 2 else list(fund_dict.keys())
    )
    
    if len(selected_funds) < 2:
        st.warning("Please select at least 2 funds to compare")
        return
    
    selected_fund_ids = [fund_dict[name] for name in selected_funds]
    
    # Get data for selected funds
    compare_df = df[df['FUND_ID'].isin(selected_fund_ids)]
    
    # Comparison table
    st.markdown("### 📋 Side-by-Side Comparison")
    
    metrics = [
        ('TOTAL_ASSETS', 'Total Assets (M)', ',.2f'),
        ('AVG_ANNUAL_MANAGEMENT_FEE', 'Management Fee (%)', '.2f'),
        ('AVG_DEPOSIT_FEE', 'Deposit Fee (%)', '.2f'),
        ('MONTHLY_YIELD', 'Monthly Yield (%)', '.2f'),
        ('YEAR_TO_DATE_YIELD', 'YTD Yield (%)', '.2f'),
        ('AVG_ANNUAL_YIELD_TRAILING_3YRS', '3Y Avg Yield (%)', '.2f'),
        ('AVG_ANNUAL_YIELD_TRAILING_5YRS', '5Y Avg Yield (%)', '.2f'),
        ('STANDARD_DEVIATION', 'Std Deviation', '.2f'),
        ('SHARPE_RATIO', 'Sharpe Ratio', '.2f'),
        ('STOCK_MARKET_EXPOSURE', 'Stock Exposure (%)', '.2f'),
        ('FOREIGN_EXPOSURE', 'Foreign Exposure (%)', '.2f'),
    ]
    
    comparison_data = {'Metric': [m[1] for m in metrics]}
    
    for fund_name in selected_funds:
        fund_id = fund_dict[fund_name]
        fund_row = compare_df[compare_df['FUND_ID'] == fund_id].iloc[0] if len(compare_df[compare_df['FUND_ID'] == fund_id]) > 0 else None
        
        values = []
        for col, label, fmt in metrics:
            if fund_row is not None and pd.notna(fund_row[col]):
                values.append(f"{fund_row[col]:{fmt}}")
            else:
                values.append("N/A")
        
        # Truncate fund name for column header
        short_name = fund_name[:25] + "..." if len(fund_name) > 25 else fund_name
        comparison_data[short_name] = values
    
    comparison_table = pd.DataFrame(comparison_data)
    st.dataframe(comparison_table, use_container_width=True, hide_index=True)
    
    # Historical comparison chart
    st.markdown("### 📈 Historical Performance")
    
    historical_df = all_df[all_df['FUND_ID'].isin(selected_fund_ids)].copy()
    
    if len(historical_df) > 0:
        fig = px.line(
            historical_df,
            x='REPORT_DATE',
            y='MONTHLY_YIELD',
            color='FUND_NAME',
            title='Monthly Yield Over Time',
            labels={'REPORT_DATE': 'Date', 'MONTHLY_YIELD': 'Monthly Yield (%)', 'FUND_NAME': 'Fund'},
            color_discrete_sequence=COLORS
        )
        fig.update_layout(height=400, legend=dict(orientation="h", yanchor="bottom", y=-0.3))
        st.plotly_chart(fig, use_container_width=True)
        
        # Assets over time
        fig2 = px.line(
            historical_df,
            x='REPORT_DATE',
            y='TOTAL_ASSETS',
            color='FUND_NAME',
            title='Total Assets Over Time',
            labels={'REPORT_DATE': 'Date', 'TOTAL_ASSETS': 'Total Assets (M)', 'FUND_NAME': 'Fund'},
            color_discrete_sequence=COLORS
        )
        fig2.update_layout(height=400, legend=dict(orientation="h", yanchor="bottom", y=-0.3))
        st.plotly_chart(fig2, use_container_width=True)


def render_historical(all_df):
    """Render the historical trends tab."""
    st.subheader("📈 Historical Trends")
    
    # Fund selector
    fund_options = all_df[['FUND_ID', 'FUND_NAME']].drop_duplicates()
    fund_dict = dict(zip(fund_options['FUND_NAME'], fund_options['FUND_ID']))
    
    selected_fund = st.selectbox(
        "Select a fund to view history",
        options=list(fund_dict.keys())
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
        if len(fund_history) > 1:
            asset_growth = ((latest['TOTAL_ASSETS'] - fund_history.iloc[0]['TOTAL_ASSETS']) / fund_history.iloc[0]['TOTAL_ASSETS'] * 100)
            st.metric("Asset Growth", f"{asset_growth:.1f}%")
        else:
            st.metric("Asset Growth", "N/A")
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Monthly Yield', 'Total Assets', 'Year-to-Date Yield', 'Management Fee'),
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )
    
    # Monthly Yield
    fig.add_trace(
        go.Scatter(x=fund_history['REPORT_DATE'], y=fund_history['MONTHLY_YIELD'],
                   mode='lines+markers', name='Monthly Yield', line=dict(color=COLORS[0])),
        row=1, col=1
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    
    # Total Assets
    fig.add_trace(
        go.Scatter(x=fund_history['REPORT_DATE'], y=fund_history['TOTAL_ASSETS'],
                   mode='lines+markers', name='Total Assets', line=dict(color=COLORS[1]),
                   fill='tozeroy', fillcolor='rgba(124, 58, 237, 0.1)'),
        row=1, col=2
    )
    
    # YTD Yield
    fig.add_trace(
        go.Scatter(x=fund_history['REPORT_DATE'], y=fund_history['YEAR_TO_DATE_YIELD'],
                   mode='lines+markers', name='YTD Yield', line=dict(color=COLORS[2])),
        row=2, col=1
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
    
    # Management Fee
    fig.add_trace(
        go.Scatter(x=fund_history['REPORT_DATE'], y=fund_history['AVG_ANNUAL_MANAGEMENT_FEE'],
                   mode='lines+markers', name='Mgmt Fee', line=dict(color=COLORS[3])),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False, title_text=f"📊 {selected_fund}")
    fig.update_xaxes(tickangle=45)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistics table
    st.markdown("### 📊 Statistics Summary")
    
    stats_data = {
        'Metric': ['Monthly Yield (%)', 'Total Assets (M)', 'Management Fee (%)', 'Stock Exposure (%)'],
        'Min': [
            f"{fund_history['MONTHLY_YIELD'].min():.2f}",
            f"{fund_history['TOTAL_ASSETS'].min():.2f}",
            f"{fund_history['AVG_ANNUAL_MANAGEMENT_FEE'].min():.2f}" if fund_history['AVG_ANNUAL_MANAGEMENT_FEE'].notna().any() else "N/A",
            f"{fund_history['STOCK_MARKET_EXPOSURE'].min():.2f}" if fund_history['STOCK_MARKET_EXPOSURE'].notna().any() else "N/A",
        ],
        'Max': [
            f"{fund_history['MONTHLY_YIELD'].max():.2f}",
            f"{fund_history['TOTAL_ASSETS'].max():.2f}",
            f"{fund_history['AVG_ANNUAL_MANAGEMENT_FEE'].max():.2f}" if fund_history['AVG_ANNUAL_MANAGEMENT_FEE'].notna().any() else "N/A",
            f"{fund_history['STOCK_MARKET_EXPOSURE'].max():.2f}" if fund_history['STOCK_MARKET_EXPOSURE'].notna().any() else "N/A",
        ],
        'Average': [
            f"{fund_history['MONTHLY_YIELD'].mean():.2f}",
            f"{fund_history['TOTAL_ASSETS'].mean():.2f}",
            f"{fund_history['AVG_ANNUAL_MANAGEMENT_FEE'].mean():.2f}" if fund_history['AVG_ANNUAL_MANAGEMENT_FEE'].notna().any() else "N/A",
            f"{fund_history['STOCK_MARKET_EXPOSURE'].mean():.2f}" if fund_history['STOCK_MARKET_EXPOSURE'].notna().any() else "N/A",
        ],
        'Std Dev': [
            f"{fund_history['MONTHLY_YIELD'].std():.2f}",
            f"{fund_history['TOTAL_ASSETS'].std():.2f}",
            f"{fund_history['AVG_ANNUAL_MANAGEMENT_FEE'].std():.2f}" if fund_history['AVG_ANNUAL_MANAGEMENT_FEE'].notna().any() else "N/A",
            f"{fund_history['STOCK_MARKET_EXPOSURE'].std():.2f}" if fund_history['STOCK_MARKET_EXPOSURE'].notna().any() else "N/A",
        ],
    }
    
    st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)


def main():
    # Fetch data
    with st.spinner("Fetching data from data.gov.il..."):
        all_df = fetch_all_data()
    
    if all_df.empty:
        st.error("Failed to fetch data. Please try again later.")
        return
    
    # Get available periods
    periods = sorted(all_df['REPORT_PERIOD'].unique(), reverse=True)
    latest_period = periods[0]
    
    # Sidebar filters
    st.sidebar.header("🔧 Filters")
    
    # Period selector
    selected_period = st.sidebar.selectbox(
        "📅 Report Period",
        options=periods,
        index=0,
        format_func=format_period
    )
    
    # Filter data by selected period
    filtered_df = all_df[all_df['REPORT_PERIOD'] == selected_period].copy()
    
    # Classification filter
    classifications = ['All'] + sorted(filtered_df['FUND_CLASSIFICATION'].unique().tolist())
    selected_classification = st.sidebar.selectbox(
        "📁 Fund Classification",
        options=classifications
    )
    
    if selected_classification != 'All':
        filtered_df = filtered_df[filtered_df['FUND_CLASSIFICATION'] == selected_classification]
    
    # Managing corporation filter
    corporations = ['All'] + sorted(filtered_df['MANAGING_CORPORATION'].dropna().unique().tolist())
    selected_corp = st.sidebar.selectbox(
        "🏢 Managing Corporation",
        options=corporations
    )
    
    if selected_corp != 'All':
        filtered_df = filtered_df[filtered_df['MANAGING_CORPORATION'] == selected_corp]
    
    # Minimum assets filter
    min_assets = st.sidebar.slider(
        "💰 Minimum Total Assets (M)",
        min_value=0.0,
        max_value=float(filtered_df['TOTAL_ASSETS'].max()) if len(filtered_df) > 0 else 100.0,
        value=0.0,
        step=10.0
    )
    
    if min_assets > 0:
        filtered_df = filtered_df[filtered_df['TOTAL_ASSETS'] >= min_assets]
    
    # Stock Market Exposure filter (now in percentages 0-100%)
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📈 Exposure Filters**")
    
    stock_exposure_range = st.sidebar.slider(
        "📊 Stock Market Exposure (%)",
        min_value=0.0,
        max_value=100.0,
        value=(0.0, 100.0),
        step=1.0
    )
    filtered_df = filtered_df[
        (filtered_df['STOCK_MARKET_EXPOSURE'] >= stock_exposure_range[0]) & 
        (filtered_df['STOCK_MARKET_EXPOSURE'] <= stock_exposure_range[1])
    ]
    
    # Foreign Exposure filter (now in percentages 0-100%)
    foreign_exposure_range = st.sidebar.slider(
        "🌍 Foreign Exposure (%)",
        min_value=0.0,
        max_value=100.0,
        value=(0.0, 100.0),
        step=1.0
    )
    filtered_df = filtered_df[
        (filtered_df['FOREIGN_EXPOSURE'] >= foreign_exposure_range[0]) & 
        (filtered_df['FOREIGN_EXPOSURE'] <= foreign_exposure_range[1])
    ]
    
    # Foreign Currency Exposure filter (now in percentages 0-100%)
    currency_exposure_range = st.sidebar.slider(
        "💱 Foreign Currency Exposure (%)",
        min_value=0.0,
        max_value=100.0,
        value=(0.0, 100.0),
        step=1.0
    )
    filtered_df = filtered_df[
        (filtered_df['FOREIGN_CURRENCY_EXPOSURE'] >= currency_exposure_range[0]) & 
        (filtered_df['FOREIGN_CURRENCY_EXPOSURE'] <= currency_exposure_range[1])
    ]
    
    # Fund name search
    search_term = st.sidebar.text_input("🔍 Search Fund Name", "")
    if search_term:
        filtered_df = filtered_df[filtered_df['FUND_NAME'].str.contains(search_term, case=False, na=False)]
    
    # Refresh button in sidebar
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Data Table", "📊 Charts", "⚖️ Compare Funds", "📈 Historical Trends"])
    
    with tab1:
        st.subheader(f"📋 Pension Funds - {format_period(selected_period)}")
        render_data_table(filtered_df, selected_period, all_df)
    
    with tab2:
        render_charts(filtered_df)
    
    with tab3:
        render_comparison(filtered_df, all_df)
    
    with tab4:
        render_historical(all_df)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #64748b; font-size: 0.85rem;">
            Data source: <a href="https://data.gov.il" target="_blank">data.gov.il</a> | 
            Resource ID: 6d47d6b5-cb08-488b-b333-f1e717b1e1bd |
            Last updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M') + """
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
