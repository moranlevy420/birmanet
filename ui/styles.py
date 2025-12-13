"""
Centralized CSS styles for the application.
"""

# Main application CSS
APP_CSS = """
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
"""


def get_page_config() -> dict:
    """Get Streamlit page configuration."""
    return {
        "page_title": "Find Better",
        "page_icon": "📊",
        "layout": "wide",
        "initial_sidebar_state": "expanded",
        "menu_items": {
            'About': """
## 📊 Find Better - Pension Explorer

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
    }

