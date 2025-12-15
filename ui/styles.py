"""
Centralized CSS styles for the application.
"""

# Main application CSS with professional polish
APP_CSS = """
<style>
    /* ========== GLOBAL TRANSITIONS & ANTI-FLICKER ========== */
    
    /* Smooth transitions for all elements */
    * {
        transition: opacity 0.15s ease-in-out, background-color 0.15s ease-in-out;
    }
    
    /* Prevent layout shift during loading */
    .main .block-container {
        opacity: 1;
        animation: fadeIn 0.2s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0.7; }
        to { opacity: 1; }
    }
    
    /* Hide Streamlit branding */
    .stDeployButton,
    [data-testid="stDecoration"],
    button[kind="header"],
    .stAppDeployButton,
    #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* ========== HEADER & LAYOUT ========== */
    
    header[data-testid="stHeader"] {
        height: 2.5rem !important;
        min-height: 2.5rem !important;
        background: linear-gradient(90deg, #1e3a5f 0%, #2563eb 100%);
    }
    
    .block-container {
        padding-top: 2.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    
    /* ========== TAB STYLING ========== */
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: #e2e8f0;
        padding: 0.5rem;
        border-radius: 0.5rem;
        display: flex;
        flex-wrap: nowrap;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 600;
        padding: 0.5rem 1rem;
        background-color: #f8fafc;
        border-radius: 0.3rem;
        color: #334155 !important;
        transition: all 0.15s ease-in-out !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #dbeafe !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1e40af !important;
        color: white !important;
        box-shadow: 0 2px 4px rgba(30, 64, 175, 0.3);
    }
    
    .stTabs button[data-baseweb="tab"] p {
        color: inherit !important;
    }
    
    /* Push About and Settings tabs to far right */
    .stTabs [data-baseweb="tab-list"] > button:nth-child(7) {
        margin-right: auto !important;
    }
    
    /* Style About (8th) and Settings (9th) differently */
    .stTabs [data-baseweb="tab-list"] > button:nth-child(8),
    .stTabs [data-baseweb="tab-list"] > button:nth-child(9) {
        background-color: transparent !important;
        border: 1px solid #94a3b8 !important;
        color: #64748b !important;
        font-weight: 500 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] > button:nth-child(8)[aria-selected="true"],
    .stTabs [data-baseweb="tab-list"] > button:nth-child(9)[aria-selected="true"] {
        background-color: #475569 !important;
        border-color: #475569 !important;
        color: white !important;
    }
    
    /* Tab content - prevent flicker */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
        min-height: 400px;
    }
    
    /* ========== AGGRID TABLE ANTI-FLICKER ========== */
    
    .ag-root-wrapper {
        min-height: 280px !important;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    iframe[title="streamlit_aggrid.agGrid"] {
        min-height: 280px !important;
    }
    
    /* Stable table container */
    [data-testid="stHorizontalBlock"] {
        min-height: 50px;
    }
    
    /* Enable text selection in AgGrid */
    .ag-cell {
        user-select: text !important;
        -webkit-user-select: text !important;
    }
    
    /* ========== SIDEBAR ========== */
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.5rem !important;
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    [data-testid="stSidebar"] {
        min-width: 280px !important;
        max-width: 280px !important;
        box-shadow: 2px 0 8px rgba(0,0,0,0.05);
    }
    
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
    
    /* ========== CHARTS ========== */
    
    /* Stable chart containers */
    [data-testid="stPlotlyChart"] {
        min-height: 300px;
    }
    
    /* ========== LOADING STATES ========== */
    
    .stSpinner > div {
        border-color: #2563eb !important;
    }
    
    /* ========== PRINT STYLES ========== */
    
    @media print {
        [data-testid="stSidebar"],
        [data-testid="stHeader"],
        .stDeployButton,
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

