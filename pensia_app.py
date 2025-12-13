"""
Pension Funds Explorer - Interactive Dashboard
Fetches and displays pension fund data from data.gov.il

Run with: streamlit run pensia_app.py
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

# Data cache settings
CACHE_DB_PATH = Path(__file__).parent / "fund_cache.db"
CACHE_MAX_AGE_HOURS = 24  # Re-fetch from API after 24 hours

# Column state persistence
COLUMN_STATE_PATH = Path(__file__).parent / "column_state.json"

# GitHub update settings
GITHUB_REPO = "moranlevy420/birmanet"
GITHUB_BRANCH = "main"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"
UPDATE_FILES = ["pensia_app.py", "requirements.txt", "run_app.bat", "INSTALL_WINDOWS.bat", "UNINSTALL_WINDOWS.bat", "UPDATE_WINDOWS.bat"]

# Page configuration
st.set_page_config(
    page_title="Find Better",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': """
## 📊 Pension Funds Explorer

**📅 Report Period** - Select which month's data to view.

**📁 Filters** - Narrow down funds by type, company, or exposure levels.

**📋 World View**
- Click column headers to sort
- Download data with 📥 CSV button

**📈 Chart** - Shows top 5 funds over time.
- Hover dots to see values
- Change range: 12M, 24M, 36M, All

**🔄 Refresh Data** - Fetches latest data from the internet.

---
**Columns:**
- YTD = Year-to-date return
- Mgmt Fee = Annual fee
- Sharpe = Risk-adjusted return
- Stock Exp. = % in stocks
- Foreign Exp. = % in foreign assets

---
Data source: [data.gov.il](https://data.gov.il)
        """
    }
)

# Custom CSS for better styling - reduce padding
st.markdown("""
<style>
    /* Hide Deploy button and App View button */
    .stDeployButton,
    [data-testid="stDecoration"],
    button[kind="header"],
    .stAppDeployButton {
        display: none !important;
        visibility: hidden !important;
    }
    /* Reduce header height */
    header[data-testid="stHeader"] {
        height: 2.5rem !important;
        min-height: 2.5rem !important;
    }
    .block-container {
        padding-top: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    /* Tab styling - darker, more readable */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: #e2e8f0;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 600;
        padding: 0.5rem 1rem;
        background-color: #f8fafc;
        border-radius: 0.3rem;
        color: #334155 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e40af !important;
        color: white !important;
    }
    .stTabs button[data-baseweb="tab"] p {
        color: inherit !important;
    }
    
    /* Prevent AgGrid flickering */
    .ag-root-wrapper {
        min-height: 280px !important;
    }
    iframe[title="streamlit_aggrid.agGrid"] {
        min-height: 280px !important;
    }
    
    /* Enable text selection in AgGrid */
    .ag-cell {
        user-select: text !important;
        -webkit-user-select: text !important;
        -moz-user-select: text !important;
        -ms-user-select: text !important;
    }
    
    /* Reduce sidebar padding and width */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.5rem !important;
    }
    [data-testid="stSidebar"] {
        min-width: 280px !important;
        max-width: 280px !important;
    }
    /* Reduce vertical spacing in sidebar */
    [data-testid="stSidebar"] .stMarkdown {
        margin-bottom: 0 !important;
    }
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stMultiSelect,
    [data-testid="stSidebar"] .stSlider,
    [data-testid="stSidebar"] .stTextInput {
        margin-bottom: 0.5rem !important;
    }
    [data-testid="stSidebar"] h3 {
        margin-bottom: 0.5rem !important;
        margin-top: 0 !important;
    }
    [data-testid="stSidebar"] hr {
        margin: 0.5rem 0 !important;
    }
    
    /* Hide sidebar and header when printing */
    @media print {
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stHeader"] {
            display: none !important;
        }
        .stDeployButton {
            display: none !important;
        }
        [data-testid="stToolbar"] {
            display: none !important;
        }
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# App Version
VERSION = "1.3.0"


def check_for_updates():
    """Check GitHub for a newer version."""
    try:
        # Fetch the latest pensia_app.py to get the version
        response = requests.get(f"{GITHUB_RAW_URL}/pensia_app.py", timeout=5)
        if response.status_code == 200:
            content = response.text
            # Extract VERSION from the file
            for line in content.split('\n'):
                if line.startswith('VERSION = '):
                    remote_version = line.split('"')[1]
                    return remote_version, remote_version != VERSION
        return None, False
    except Exception:
        return None, False


def download_updates():
    """Download and apply updates from GitHub."""
    app_dir = Path(__file__).parent
    updated_files = []
    errors = []
    
    for filename in UPDATE_FILES:
        try:
            response = requests.get(f"{GITHUB_RAW_URL}/{filename}", timeout=30)
            if response.status_code == 200:
                file_path = app_dir / filename
                # Write the new content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                updated_files.append(filename)
            else:
                errors.append(f"{filename}: HTTP {response.status_code}")
        except Exception as e:
            errors.append(f"{filename}: {str(e)}")
    
    return updated_files, errors


def parse_version(version_str):
    """Parse version string to tuple for comparison."""
    try:
        parts = version_str.split('.')
        return tuple(int(p) for p in parts)
    except:
        return (0, 0, 0)


def is_newer_version(remote_version, local_version):
    """Check if remote version is newer than local version."""
    return parse_version(remote_version) > parse_version(local_version)


# API Configuration
DATASETS = {
    "pension": {
        "name": "Pension Funds",
        "name_heb": "קרנות פנסיה",
        "resource_ids": [
            "6d47d6b5-cb08-488b-b333-f1e717b1e1bd",  # 2024-2025 data
            "4694d5a7-5284-4f3d-a2cb-5887f43fb55e",  # 2023 data
        ],
        "sub_filters": {
            "column": "FUND_CLASSIFICATION",
            "options": ["קרנות חדשות", "קרנות כלליות"]
        }
    },
    "kupot_gemel": {
        "name": "Kupot Gemel",
        "name_heb": "קופות גמל",
        "resource_ids": [
            "a30dcbea-a1d2-482c-ae29-8f781f5025fb",  # Gemel 2024-2025 data
            "2016d770-f094-4a2e-983e-797c26479720",  # Gemel 2023 data
        ],
        "filter": {"FUND_CLASSIFICATION": ["תגמולים ואישית לפיצויים"]},
        "population_filter": {
            "column": "TARGET_POPULATION",
            "exclude_values": ["עובדי סקטור מסויים", "עובדי מפעל/גוף מסויים"]
        }
    },
    "hishtalmut": {
        "name": "Hishtalmut",
        "name_heb": "קרנות השתלמות",
        "resource_ids": [
            "a30dcbea-a1d2-482c-ae29-8f781f5025fb",  # Gemel 2024-2025 data
            "2016d770-f094-4a2e-983e-797c26479720",  # Gemel 2023 data
        ],
        "filter": {"FUND_CLASSIFICATION": ["קרנות השתלמות"]},
        "population_filter": {
            "column": "TARGET_POPULATION",
            "exclude_values": ["עובדי סקטור מסויים", "עובדי מפעל/גוף מסויים"]
        }
    },
    "investment_gemel": {
        "name": "Investment Gemel",
        "name_heb": "קופות גמל להשקעה",
        "resource_ids": [
            "a30dcbea-a1d2-482c-ae29-8f781f5025fb",  # Gemel 2024-2025 data
            "2016d770-f094-4a2e-983e-797c26479720",  # Gemel 2023 data
        ],
        "filter": {"FUND_CLASSIFICATION": ["קופת גמל להשקעה", "קופת גמל להשקעה - חסכון לילד"]},
        "sub_filters": {
            "column": "FUND_CLASSIFICATION",
            "options": ["קופת גמל להשקעה", "קופת גמל להשקעה - חסכון לילד"]
        }
    },
    "insurance": {
        "name": "Insurance Funds",
        "name_heb": "ביטוח מנהלים",
        "resource_ids": [
            "c6c62cc7-fe02-4b18-8f3e-813abfbb4647",  # Insurance 2024-2025 data
            "672090ba-7893-4496-a07c-dc7e822cbf18",  # Insurance 2023 data
        ],
        "sub_filters": {
            "column": "FUND_CLASSIFICATION",
            "options": ["פוליסות שהונפקו בשנים 1990-1991", "פוליסות שהונפקו בשנים 1992-2003", "פוליסות שהונפקו החל משנת 2004"]
        }
    }
}
BASE_URL = "https://data.gov.il/api/3/action/datastore_search"

# Columns to display
DISPLAY_COLUMNS = [
    'FUND_ID',
    'FUND_NAME',
    'MONTHLY_YIELD',
    'YEAR_TO_DATE_YIELD',
    'AVG_ANNUAL_YIELD_TRAILING_3YRS',
    'AVG_ANNUAL_YIELD_TRAILING_5YRS',
    'SHARPE_RATIO',
    'STANDARD_DEVIATION',
    'TOTAL_ASSETS',
    'STOCK_MARKET_EXPOSURE',
    'FOREIGN_EXPOSURE',
    'FOREIGN_CURRENCY_EXPOSURE',
    'LIQUID_ASSETS_PERCENT',
    'AVG_ANNUAL_MANAGEMENT_FEE',
    'AVG_DEPOSIT_FEE',
    'FUND_CLASSIFICATION',
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


def save_column_order(column_order):
    """Save column order to JSON file."""
    try:
        with open(COLUMN_STATE_PATH, 'w') as f:
            json.dump({'column_order': column_order}, f)
    except Exception:
        pass


def load_column_order():
    """Load column order from JSON file."""
    if not COLUMN_STATE_PATH.exists():
        return None
    try:
        with open(COLUMN_STATE_PATH, 'r') as f:
            data = json.load(f)
            return data.get('column_order')
    except Exception:
        return None


def get_cache_age(dataset_type="pension"):
    """Get age of cached data in hours."""
    if not CACHE_DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key = ?", (f'last_updated_{dataset_type}',))
        result = cursor.fetchone()
        conn.close()
        if result:
            last_updated = datetime.fromisoformat(result[0])
            age = datetime.now() - last_updated
            return age.total_seconds() / 3600
    except:
        pass
    return None


def save_to_cache(df, dataset_type="pension"):
    """Save DataFrame to SQLite cache."""
    conn = sqlite3.connect(CACHE_DB_PATH)
    
    # Save data
    table_name = f'{dataset_type}_data'
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    # Save metadata
    conn.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", 
                 (f'last_updated_{dataset_type}', datetime.now().isoformat()))
    conn.commit()
    conn.close()


def load_from_cache(dataset_type="pension"):
    """Load DataFrame from SQLite cache."""
    if not CACHE_DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(CACHE_DB_PATH)
        table_name = f'{dataset_type}_data'
        df = pd.read_sql(f'SELECT * FROM {table_name}', conn)
        conn.close()
        # Restore datetime column
        df['REPORT_DATE'] = pd.to_datetime(df['REPORT_DATE'])
        return df
    except Exception as e:
        return None


def fetch_from_api(dataset_type="pension"):
    """Fetch fund data from API."""
    all_records = []
    resource_ids = DATASETS[dataset_type]["resource_ids"]
    
    for resource_id in resource_ids:
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
    
    # Apply filter if defined for this dataset
    dataset_filter = DATASETS[dataset_type].get("filter")
    if dataset_filter and not df.empty:
        for col, values in dataset_filter.items():
            if col in df.columns:
                df = df[df[col].isin(values)]
    
    # Fix encoding issues in FUND_NAME (e.g., S1;P500 -> S&P500)
    if 'FUND_NAME' in df.columns:
        df['FUND_NAME'] = df['FUND_NAME'].str.replace('1;', '&', regex=False)
        df['FUND_NAME'] = df['FUND_NAME'].str.replace('&amp;', '&', regex=False)
    
    # Remove IRA funds (בניהול אישי - self-managed) from all products
    if 'FUND_NAME' in df.columns and not df.empty:
        df = df[~df['FUND_NAME'].str.contains('בניהול אישי', na=False)]
    
    # Remove duplicates (same FUND_ID and REPORT_PERIOD)
    df = df.drop_duplicates(subset=['FUND_ID', 'REPORT_PERIOD'], keep='first')
    
    # Create date column for plotting
    df['REPORT_DATE'] = pd.to_datetime(df['REPORT_PERIOD'].astype(str), format='%Y%m')
    
    # Check if exposure values need conversion (if max > 100, they're absolute values)
    exposure_cols = ['STOCK_MARKET_EXPOSURE', 'FOREIGN_EXPOSURE', 'FOREIGN_CURRENCY_EXPOSURE']
    for col in exposure_cols:
        if col in df.columns:
            if df[col].max() > 100:
                df[col] = (df[col] / df['TOTAL_ASSETS'] * 100).round(2)
    
    return df


@st.cache_data(ttl=3600)
def fetch_all_data(dataset_type="pension", force_refresh=False):
    """Fetch data from cache or API."""
    cache_age = get_cache_age(dataset_type)
    
    # Use cache if exists and not too old
    if not force_refresh and cache_age is not None and cache_age < CACHE_MAX_AGE_HOURS:
        df = load_from_cache(dataset_type)
        if df is not None:
            return df
    
    # Fetch from API
    df = fetch_from_api(dataset_type)
    
    # Save to cache
    if not df.empty:
        save_to_cache(df, dataset_type)
    
    return df


def format_period(period: int) -> str:
    """Format period number to readable string."""
    year = period // 100
    month = period % 100
    months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    return f"{months[month]} {year}"


def render_data_table(df, selected_period, all_df, dataset_type="pension"):
    """Render the main data table tab."""
    dataset_name = DATASETS[dataset_type]["name"]
    
    # Initialize session state for sort if not exists
    if 'sort_column' not in st.session_state:
        st.session_state.sort_column = 'YTD Yield (%)'
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = 'Descending'
    
    # Pre-warm the grid to avoid first-sort flicker
    if 'grid_initialized' not in st.session_state:
        st.session_state.grid_initialized = True
        st.rerun()
    
    # Prepare display dataframe
    display_df = df[DISPLAY_COLUMNS].copy()
    display_df = display_df.rename(columns=COLUMN_LABELS)
    
    # Sort by default column before passing to AgGrid
    sort_column = st.session_state.sort_column
    sort_ascending = st.session_state.sort_order == "Ascending"
    display_df = display_df.sort_values(by=sort_column, ascending=sort_ascending, na_position='last')
    display_df = display_df.reset_index(drop=True)
    
    # Title and Download button on same row
    col_title, col_download = st.columns([4, 1])
    with col_title:
        st.subheader(f"📋 {dataset_name} - {format_period(selected_period)}")
    with col_download:
        csv = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV",
            data=csv,
            file_name=f"pension_funds_{selected_period}.csv",
            mime="text/csv",
            key="download_csv_btn"
        )
    
    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(display_df)
    gb.configure_default_column(
        sortable=True, 
        filter=True, 
        resizable=True,
        wrapHeaderText=True,
        autoHeaderHeight=True,
        width=90
    )
    gb.configure_column("Fund ID", width=70, pinned="left")
    gb.configure_column("Fund Name", width=180, wrapHeaderText=False, pinned="left", 
                        cellStyle={'direction': 'rtl', 'textAlign': 'right'})
    gb.configure_column("Classification", width=100,
                        cellStyle={'direction': 'rtl', 'textAlign': 'right'})
    
    # Set default sort
    sort_column = st.session_state.sort_column
    sort_order = st.session_state.sort_order
    sort_asc = sort_order == "Ascending"
    gb.configure_column(sort_column, sort=("asc" if sort_asc else "desc"))
    
    # Enable column moving and text selection
    gb.configure_grid_options(
        suppressDragLeaveHidesColumns=True,
        enableCellTextSelection=True,
        ensureDomOrder=True
    )
    
    grid_options = gb.build()
    
    # Display AgGrid table - key includes data hash to refresh on filter changes
    data_hash = hash(tuple(display_df['Fund ID'].tolist())) if len(display_df) > 0 else 0
    grid_response = AgGrid(
        display_df,
        gridOptions=grid_options,
        height=280,
        update_mode=GridUpdateMode.SORTING_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        theme="streamlit",
        allow_unsafe_jscode=True,
        key=f"pension_grid_{len(display_df)}_{data_hash}"
    )
    
    # Get sorted data from grid
    sorted_df = pd.DataFrame(grid_response['data']) if grid_response['data'] is not None else display_df
    
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
    
    # Get top 5 fund IDs from the sorted table (in order)
    top5_display = sorted_df.head(5)
    top5_fund_names = top5_display['Fund Name'].tolist()
    
    # Get fund IDs in the same order as table
    fund_name_to_id = df.set_index('FUND_NAME')['FUND_ID'].to_dict()
    top5_fund_ids = [fund_name_to_id.get(name) for name in top5_fund_names if name in fund_name_to_id]
    
    # Get historical data for these funds
    historical_df = all_df[all_df['FUND_ID'].isin(top5_fund_ids)].copy()
    
    # Set FUND_NAME as categorical with order matching table
    historical_df['FUND_NAME'] = pd.Categorical(
        historical_df['FUND_NAME'], 
        categories=top5_fund_names, 
        ordered=True
    )
    
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
        
        # Create short unique fund names for hover
        historical_df = historical_df.copy()
        # Filter out NaN/None values from fund names
        unique_funds = [f for f in historical_df['FUND_NAME'].unique().tolist() if isinstance(f, str)]
        
        def get_short_unique_name(name, all_names):
            """Get shortest unique name based on words."""
            # Handle non-string names
            if not isinstance(name, str):
                return str(name)[:15] if name else "Unknown"
            
            # Filter all_names to only strings
            all_names = [n for n in all_names if isinstance(n, str)]
            
            words = name.split()
            if not words:
                return name[:15]
            
            # Try first word only
            first_word = words[0]
            matches = [n for n in all_names if n.split()[0] == first_word]
            if len(matches) == 1:
                return first_word
            
            # Try first + last word (with ... in between)
            if len(words) >= 2:
                last_word = words[-1]
                first_last = f"{first_word} ... {last_word}"
                matches = [n for n in all_names if n.split()[0] == first_word and n.split()[-1] == last_word]
                if len(matches) == 1:
                    return first_last
            
            # Try first 2 words
            if len(words) >= 2:
                two_words = ' '.join(words[:2])
                matches = [n for n in all_names if n.startswith(two_words)]
                if len(matches) == 1:
                    return two_words
            
            # Try first 2 + last word
            if len(words) >= 3:
                first_two_last = f"{words[0]} {words[1]} ... {words[-1]}"
                matches = [n for n in all_names if ' '.join(n.split()[:2]) == ' '.join(words[:2]) and n.split()[-1] == words[-1]]
                if len(matches) == 1:
                    return first_two_last
            
            # Fallback: first 3 words or full name if short
            result = ' '.join(words[:3])
            return result if len(result) <= 25 else result[:22] + '..'
        
        short_name_map = {name: get_short_unique_name(name, unique_funds) for name in unique_funds}
        historical_df['SHORT_NAME'] = historical_df['FUND_NAME'].map(short_name_map)
        
        # Dynamic chart showing the sorted column over time
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
        # Update hover template to show short fund name, date, and value
        fig.update_traces(
            mode='lines+markers',
            hovertemplate='<b>%{customdata[0]}</b><br>%{x|%Y/%m}: %{y:.2f}%<extra></extra>'
        )
        fig.update_layout(
            height=320,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                font=dict(size=10)
            ),
            margin=dict(t=30, b=80, r=150, l=50),
            xaxis=dict(
                tickformat='%Y/%m',
                tickmode='array',
                tickvals=historical_df['REPORT_DATE'].unique(),
                tickangle=-45,
                showticklabels=True,
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                gridwidth=1
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.3)',
                gridwidth=1,
                zeroline=True,
                zerolinecolor='rgba(128,128,128,0.5)'
            ),
            hovermode='closest'
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        # Key includes all factors that affect the chart
        chart_key = f"top5_chart_{selected_period}_{sort_column}_{sort_order}_{months_range}_{'-'.join(map(str, top5_fund_ids))}"
        st.plotly_chart(fig, use_container_width=True, key=chart_key)
    else:
        st.info("No historical data available for the selected funds.")


def apply_chart_style(fig, height=400, show_legend=True, is_time_series=False, historical_df=None):
    """Apply consistent chart styling across all charts."""
    layout_opts = {
        'height': height,
        'hovermode': 'closest',
        'yaxis': dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.3)',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='rgba(128,128,128,0.5)'
        )
    }
    
    if show_legend:
        layout_opts['legend'] = dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=10)
        )
        layout_opts['margin'] = dict(t=50, b=80, r=150, l=50)
    else:
        layout_opts['showlegend'] = False
        layout_opts['margin'] = dict(t=50, b=80, r=30, l=50)
    
    if is_time_series and historical_df is not None:
        layout_opts['xaxis'] = dict(
            tickformat='%Y/%m',
            tickmode='array',
            tickvals=historical_df['REPORT_DATE'].unique() if 'REPORT_DATE' in historical_df.columns else None,
            tickangle=-45,
            showticklabels=True,
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            gridwidth=1
        )
    else:
        layout_opts['xaxis'] = dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            gridwidth=1
        )
    
    fig.update_layout(**layout_opts)
    return fig


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
        fig1.update_traces(hovertemplate='<b>%{y}</b><br>Yield: %{x:.2f}%<extra></extra>')
        fig1 = apply_chart_style(fig1, height=400, show_legend=False)
        fig1.update_layout(yaxis={'categoryorder': 'total ascending'})
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
        fig2.update_traces(hovertemplate='<b>%{y}</b><br>Assets: %{x:,.0f}M<extra></extra>')
        fig2 = apply_chart_style(fig2, height=400, show_legend=False)
        fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Yield vs Fee scatter
        scatter_df = df.dropna(subset=['AVG_ANNUAL_MANAGEMENT_FEE', 'MONTHLY_YIELD'])
        fig3 = px.scatter(
            scatter_df,
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
            },
            color_discrete_sequence=COLORS
        )
        fig3.update_traces(hovertemplate='<b>%{hovertext}</b><br>Fee: %{x:.2f}%<br>Yield: %{y:.2f}%<extra></extra>')
        fig3 = apply_chart_style(fig3, height=400)
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
        fig4 = apply_chart_style(fig4, height=400, show_legend=False)
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
        fig5.update_traces(hovertemplate='<b>%{label}</b><br>Assets: %{value:,.0f}M<br>%{percent}<extra></extra>')
        fig5 = apply_chart_style(fig5, height=350)
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
        fig6.update_traces(hovertemplate='<b>%{x}</b><br>Avg Yield: %{y:.2f}%<extra></extra>')
        fig6 = apply_chart_style(fig6, height=350, show_legend=False)
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
        # Create short names for hover
        unique_funds = [f for f in historical_df['FUND_NAME'].unique().tolist() if isinstance(f, str)]
        short_name_map = {name: name.split()[0] if len(name.split()) > 0 else name[:15] for name in unique_funds}
        historical_df['SHORT_NAME'] = historical_df['FUND_NAME'].map(short_name_map)
        
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
        vertical_spacing=0.18,
        horizontal_spacing=0.10
    )
    
    # Monthly Yield
    fig.add_trace(
        go.Scatter(
            x=fund_history['REPORT_DATE'], y=fund_history['MONTHLY_YIELD'],
            mode='lines+markers', name='Monthly Yield', line=dict(color=COLORS[0]),
            hovertemplate='%{x|%Y/%m}: %{y:.2f}%<extra></extra>'
        ),
        row=1, col=1
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    
    # Total Assets
    fig.add_trace(
        go.Scatter(
            x=fund_history['REPORT_DATE'], y=fund_history['TOTAL_ASSETS'],
            mode='lines+markers', name='Total Assets', line=dict(color=COLORS[1]),
            fill='tozeroy', fillcolor='rgba(124, 58, 237, 0.1)',
            hovertemplate='%{x|%Y/%m}: %{y:,.0f}M<extra></extra>'
        ),
        row=1, col=2
    )
    
    # YTD Yield
    fig.add_trace(
        go.Scatter(
            x=fund_history['REPORT_DATE'], y=fund_history['YEAR_TO_DATE_YIELD'],
            mode='lines+markers', name='YTD Yield', line=dict(color=COLORS[2]),
            hovertemplate='%{x|%Y/%m}: %{y:.2f}%<extra></extra>'
        ),
        row=2, col=1
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
    
    # Management Fee
    fig.add_trace(
        go.Scatter(
            x=fund_history['REPORT_DATE'], y=fund_history['AVG_ANNUAL_MANAGEMENT_FEE'],
            mode='lines+markers', name='Mgmt Fee', line=dict(color=COLORS[3]),
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
    # Initialize update state
    if 'update_checked' not in st.session_state:
        st.session_state.update_checked = False
        st.session_state.remote_version = None
        st.session_state.update_available = False
    
    # Sidebar header with version and update check button
    col_header, col_update = st.sidebar.columns([4, 1])
    with col_header:
        update_badge = " 🔴" if st.session_state.update_available else ""
        st.markdown(f"### 📊 Find Better `v{VERSION}`{update_badge}")
    with col_update:
        if st.button("🔄", key="check_update_btn", help="Check for updates"):
            with st.spinner("..."):
                remote_ver, _ = check_for_updates()
                st.session_state.remote_version = remote_ver
                st.session_state.update_available = remote_ver and is_newer_version(remote_ver, VERSION)
                st.session_state.update_checked = True
    
    # Show update status/button if checked
    if st.session_state.update_checked:
        if st.session_state.update_available:
            if st.sidebar.button(f"⬇️ Update to v{st.session_state.remote_version}", key="download_update_btn", type="primary", use_container_width=True):
                with st.spinner("Downloading..."):
                    updated, errors = download_updates()
                    if updated:
                        st.sidebar.success(f"✅ Updated! Restart app.")
                        st.session_state.update_available = False
                    for err in errors:
                        st.sidebar.error(err)
        else:
            st.sidebar.caption("✓ Up to date")
    
    # Product selector
    dataset_type = st.sidebar.selectbox(
        "📂 Product",
        options=list(DATASETS.keys()),
        format_func=lambda x: DATASETS[x]["name"]
    )
    dataset_name = DATASETS[dataset_type]["name"]
    
    # Sub-product filter (if available for this product)
    sub_filters_config = DATASETS[dataset_type].get("sub_filters")
    selected_sub_filters = []
    if sub_filters_config:
        st.sidebar.markdown("**📋 Sub-Product**")
        for option in sub_filters_config["options"]:
            if st.sidebar.checkbox(option, value=True, key=f"sub_{option}"):
                selected_sub_filters.append(option)
    
    # Population filter (if available for this product)
    population_filter_config = DATASETS[dataset_type].get("population_filter")
    hide_sectorial = False
    if population_filter_config:
        st.sidebar.markdown("**👥 Population**")
        hide_sectorial = st.sidebar.checkbox("Hide Sectorial", value=True, key="hide_sectorial")
    
    st.sidebar.markdown("---")
    
    # Fetch data
    with st.spinner(f"Fetching {dataset_name} data from data.gov.il..."):
        all_df = fetch_all_data(dataset_type)
    
    if all_df.empty:
        st.error("Failed to fetch data. Please try again later.")
        return
    
    # Get available periods
    periods = sorted(all_df['REPORT_PERIOD'].unique(), reverse=True)
    latest_period = periods[0]
    
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
    
    # Apply sub-dataset filter if selected
    if sub_filters_config and selected_sub_filters:
        sub_col = sub_filters_config["column"]
        if sub_col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[sub_col].isin(selected_sub_filters)]
    
    # Apply population filter if enabled
    if population_filter_config and hide_sectorial:
        pop_col = population_filter_config["column"]
        exclude_vals = population_filter_config["exclude_values"]
        if pop_col in filtered_df.columns:
            filtered_df = filtered_df[~filtered_df[pop_col].isin(exclude_vals)]
    
    # Classification filter
    classifications = ['All'] + sorted(filtered_df['FUND_CLASSIFICATION'].unique().tolist())
    selected_classification = st.sidebar.selectbox(
        "📁 Fund Classification",
        options=classifications
    )
    
    if selected_classification != 'All':
        filtered_df = filtered_df[filtered_df['FUND_CLASSIFICATION'] == selected_classification]
    
    # Managing corporation filter (only for datasets that have this column)
    corp_col = None
    if 'MANAGING_CORPORATION' in filtered_df.columns:
        corp_col = 'MANAGING_CORPORATION'
    elif 'PARENT_COMPANY_NAME' in filtered_df.columns:
        corp_col = 'PARENT_COMPANY_NAME'
    
    if corp_col:
        corporations = ['All'] + sorted(filtered_df[corp_col].dropna().unique().tolist())
        selected_corp = st.sidebar.selectbox(
            "🏢 Company",
            options=corporations
        )
        
        if selected_corp != 'All':
            filtered_df = filtered_df[filtered_df[corp_col] == selected_corp]
    
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
    
    # Cache info and Refresh button in sidebar
    cache_age = get_cache_age(dataset_type)
    if cache_age is not None:
        st.sidebar.caption(f"📦 Cache: {cache_age:.1f}h old")
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📋 World View", 
        "📊 Charts", 
        "⚖️ Compare Funds", 
        "📈 Historical Trends",
        "🔍 Find Better 🚧",
        "🤔 What If 🚧",
        "👤 Personal Zone 🚧"
    ])
    
    with tab1:
        render_data_table(filtered_df, selected_period, all_df, dataset_type)
    
    with tab2:
        render_charts(filtered_df)
    
    with tab3:
        render_comparison(filtered_df, all_df)
    
    with tab4:
        render_historical(all_df)
    
    with tab5:
        st.subheader("🔍 Find Better")
        st.info("🚧 Under Construction - Coming Soon!")
        st.markdown("*Find funds that better match your criteria*")
    
    with tab6:
        st.subheader("🤔 What If")
        st.info("🚧 Under Construction - Coming Soon!")
        st.markdown("*Simulate different scenarios and compare outcomes*")
    
    with tab7:
        st.subheader("👤 Personal Zone")
        st.info("🚧 Under Construction - Coming Soon!")
        st.markdown("*Track your personal investments and preferences*")
    
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
