"""
Find Better - Pension Funds Explorer
Main application entry point.

Run with: streamlit run app.py
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
from config.settings import (
    VERSION, APP_NAME, API_BASE_URL, API_BATCH_SIZE, API_TIMEOUT,
    CACHE_DIR, CACHE_MAX_AGE_HOURS, GITHUB_RAW_URL, UPDATE_FILES,
    CONFIG_DIR
)

# Import models
from models.dataset import DatasetRegistry

# Import services
from services.cache_service import SQLiteCacheService
from services.data_service import DataService
from services.update_service import UpdateService
from services.db_service import get_db_service, init_db
from services.auth_service import AuthService

# Import UI
from ui.styles import APP_CSS, get_page_config
from ui.components.sidebar import (
    render_header, render_update_button, render_product_selector,
    render_sub_product_filter, render_population_filter,
    render_period_selector, render_classification_filter,
    render_company_filter, render_assets_filter, render_exposure_filters,
    render_search_filter, render_cache_info, render_refresh_button
)
from ui.pages.world_view import render_world_view
from ui.pages.charts_page import render_charts
from ui.pages.compare import render_comparison
from ui.pages.historical import render_historical
from ui.pages.about import render_about, render_under_construction
from ui.pages.settings import render_settings
from ui.pages.find_better import render_find_better
from services.find_better_service import FindBetterService
from ui.components.auth import check_auth, render_user_menu, is_admin, get_cookie_manager
from utils.formatters import calculate_trailing_1y_yield


def initialize_services():
    """Initialize application services."""
    # Dataset registry
    dataset_registry = DatasetRegistry(CONFIG_DIR / "datasets.json")
    
    # Cache service
    cache_service = SQLiteCacheService(
        cache_dir=CACHE_DIR,
        max_age_hours=CACHE_MAX_AGE_HOURS
    )
    
    # Data service
    data_service = DataService(
        cache_service=cache_service,
        api_base_url=API_BASE_URL,
        batch_size=API_BATCH_SIZE,
        timeout=API_TIMEOUT
    )
    
    # Update service
    update_service = UpdateService(
        app_dir=Path(__file__).parent,
        github_raw_url=GITHUB_RAW_URL,
        current_version=VERSION,
        update_files=UPDATE_FILES
    )
    
    return dataset_registry, data_service, update_service


def apply_filters(df, dataset, selected_sub_filters, hide_sectorial,
                  selected_classification, selected_corp, corp_col,
                  min_assets, exposure_ranges, search_term):
    """Apply all filters to the dataframe."""
    filtered_df = df.copy()
    
    # Apply sub-product filter
    if dataset.sub_filters and selected_sub_filters:
        col = dataset.sub_filters.column
        if col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[col].isin(selected_sub_filters)]
    
    # Apply population filter
    if dataset.population_filter and hide_sectorial:
        col = dataset.population_filter.column
        exclude_vals = dataset.population_filter.exclude_values
        if col in filtered_df.columns:
            filtered_df = filtered_df[~filtered_df[col].isin(exclude_vals)]
    
    # Classification filter
    if selected_classification != 'All' and 'FUND_CLASSIFICATION' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['FUND_CLASSIFICATION'] == selected_classification]
    
    # Company filter
    if selected_corp != 'All' and corp_col and corp_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[corp_col] == selected_corp]
    
    # Minimum assets filter
    if min_assets > 0 and 'TOTAL_ASSETS' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['TOTAL_ASSETS'] >= min_assets]
    
    # Exposure filters
    stock_range, foreign_range, currency_range = exposure_ranges
    
    if 'STOCK_MARKET_EXPOSURE' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['STOCK_MARKET_EXPOSURE'] >= stock_range[0]) &
            (filtered_df['STOCK_MARKET_EXPOSURE'] <= stock_range[1])
        ]
    
    if 'FOREIGN_EXPOSURE' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['FOREIGN_EXPOSURE'] >= foreign_range[0]) &
            (filtered_df['FOREIGN_EXPOSURE'] <= foreign_range[1])
        ]
    
    if 'FOREIGN_CURRENCY_EXPOSURE' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['FOREIGN_CURRENCY_EXPOSURE'] >= currency_range[0]) &
            (filtered_df['FOREIGN_CURRENCY_EXPOSURE'] <= currency_range[1])
        ]
    
    # Search filter
    if search_term and 'FUND_NAME' in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df['FUND_NAME'].str.contains(search_term, case=False, na=False)
        ]
    
    return filtered_df


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(**get_page_config())
    
    # Apply custom CSS
    st.markdown(APP_CSS, unsafe_allow_html=True)
    
    # Initialize session state
    if 'update_checked' not in st.session_state:
        st.session_state.update_checked = False
        st.session_state.remote_version = None
        st.session_state.update_available = False
    
    # Initialize database
    init_db()
    db_service = get_db_service()
    
    # Create auth service with session
    db_session = db_service.get_session_instance()
    auth_service = AuthService(db_session)
    find_better_service = FindBetterService(db_session)
    
    # Get cookie manager for persistent login
    cookie_manager = get_cookie_manager()
    
    # Check authentication
    current_user = check_auth(auth_service, cookie_manager)
    if not current_user:
        return  # Login form is shown
    
    # Initialize other services
    dataset_registry, data_service, update_service = initialize_services()
    
    # User menu
    render_user_menu(current_user, auth_service, cookie_manager)
    
    # Sidebar header with version
    update_badge = " 🔴" if st.session_state.get('update_available', False) else ""
    col_header, col_update = st.sidebar.columns([4, 1])
    with col_header:
        st.markdown(f"### 📊 Find Better `v{VERSION}`{update_badge}")
    with col_update:
        if st.button("🔄", key="check_update_btn", help="Check for updates"):
            with st.spinner("..."):
                remote_ver, is_available = update_service.check_for_updates()
                st.session_state.remote_version = remote_ver
                st.session_state.update_available = is_available
                st.session_state.update_checked = True
    
    # Show update button if available
    if st.session_state.get('update_checked', False):
        if st.session_state.get('update_available', False):
            remote_ver = st.session_state.get('remote_version', '')
            if st.sidebar.button(f"⬇️ Update to v{remote_ver}", type="primary", use_container_width=True):
                with st.spinner("Downloading..."):
                    updated, errors = update_service.download_updates()
                    if updated:
                        st.sidebar.success("✅ Updated! Restart app.")
                        st.session_state.update_available = False
                    for err in errors:
                        st.sidebar.error(err)
        else:
            st.sidebar.caption("✓ Up to date")
    
    # Product selector
    dataset_key = render_product_selector(dataset_registry)
    dataset = dataset_registry.get(dataset_key)
    
    # Sub-product filter
    selected_sub_filters = render_sub_product_filter(dataset)
    
    # Population filter
    hide_sectorial = render_population_filter(dataset)
    
    st.sidebar.markdown("---")
    
    # Fetch data
    with st.spinner(f"Loading {dataset.name}..."):
        all_df = data_service.get_data(dataset)
    
    if all_df.empty:
        st.error("Failed to fetch data. Please try again later.")
        return
    
    # Get available periods
    periods = sorted(all_df['REPORT_PERIOD'].unique(), reverse=True)
    
    # Period selector
    selected_period = render_period_selector(periods)
    
    # Filter data by selected period
    period_df = all_df[all_df['REPORT_PERIOD'] == selected_period].copy()
    
    # Calculate trailing 1-year yield for each fund
    period_df = calculate_trailing_1y_yield(period_df, all_df, selected_period)
    
    # Other filters
    selected_classification = render_classification_filter(period_df)
    selected_corp, corp_col = render_company_filter(period_df)
    min_assets = render_assets_filter(period_df)
    exposure_ranges = render_exposure_filters(period_df)
    search_term = render_search_filter()
    
    # Apply all filters
    filtered_df = apply_filters(
        period_df, dataset, selected_sub_filters, hide_sectorial,
        selected_classification, selected_corp, corp_col,
        min_assets, exposure_ranges, search_term
    )
    
    # Cache info
    cache_age = data_service.get_cache_age(dataset)
    render_cache_info(cache_age)
    
    # Refresh button
    if render_refresh_button():
        data_service.clear_cache(dataset)
        st.cache_data.clear()
        st.rerun()
    
    # Main content - Tabs (Settings only visible to admins)
    tab_names = [
        "📋 World View",
        "📊 Charts",
        "⚖️ Compare Funds",
        "📈 Historical Trends",
        "🔍 Find Better",
        "🤔 What If 🚧",
        "👤 Personal Zone 🚧",
        "ℹ️ About"
    ]
    if is_admin(current_user):
        tab_names.append("⚙️ Settings")
    
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        render_world_view(filtered_df, all_df, selected_period, dataset.name)
    
    with tabs[1]:
        render_charts(filtered_df)
    
    with tabs[2]:
        render_comparison(filtered_df, all_df)
    
    with tabs[3]:
        render_historical(all_df)
    
    with tabs[4]:
        render_find_better(all_df, filtered_df, selected_period, find_better_service)
    
    with tabs[5]:
        render_under_construction("🤔 What If", "Scenario analysis and projections")
    
    with tabs[6]:
        render_under_construction("👤 Personal Zone", "Track your personal investments")
    
    with tabs[7]:
        render_about()
    
    # Settings tab (admin only)
    if is_admin(current_user) and len(tabs) > 8:
        with tabs[8]:
            render_settings(auth_service, find_better_service, current_user)
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: #64748b; font-size: 0.85rem;">
            Data source: <a href="https://data.gov.il" target="_blank">data.gov.il</a> | 
            Version: {VERSION} |
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

