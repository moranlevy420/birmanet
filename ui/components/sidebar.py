"""
Sidebar components for filters and controls.
"""

import streamlit as st
import pandas as pd
from typing import List, Optional, Tuple

from models.dataset import Dataset, DatasetRegistry
from services.update_service import UpdateService
from utils.formatters import format_period


def render_header(version: str, update_available: bool) -> None:
    """Render the sidebar header with version and update button."""
    col_header, col_update = st.sidebar.columns([4, 1])
    with col_header:
        update_badge = " 🔴" if update_available else ""
        st.markdown(f"### 📊 Find Better `v{version}`{update_badge}")


def render_update_button(update_service: UpdateService) -> None:
    """Render the update check button and handle updates."""
    col_header, col_update = st.sidebar.columns([4, 1])
    
    with col_update:
        if st.button("🔄", key="check_update_btn", help="Check for updates"):
            with st.spinner("..."):
                remote_ver, is_available = update_service.check_for_updates()
                st.session_state.remote_version = remote_ver
                st.session_state.update_available = is_available
                st.session_state.update_checked = True
    
    # Show update status/button if checked
    if st.session_state.get('update_checked', False):
        if st.session_state.get('update_available', False):
            remote_ver = st.session_state.get('remote_version', '')
            if st.sidebar.button(
                f"⬇️ Update to v{remote_ver}", 
                key="download_update_btn", 
                type="primary", 
                use_container_width=True
            ):
                with st.spinner("Downloading..."):
                    updated, errors = update_service.download_updates()
                    if updated:
                        st.sidebar.success(f"✅ Updated! Restart app.")
                        st.session_state.update_available = False
                    for err in errors:
                        st.sidebar.error(err)
        else:
            st.sidebar.caption("✓ Up to date")


def render_product_selector(dataset_registry: DatasetRegistry) -> str:
    """Render product/dataset selector and return selected key."""
    return st.sidebar.selectbox(
        "📂 Product",
        options=dataset_registry.keys(),
        format_func=lambda x: dataset_registry.get(x).name
    )


def render_sub_product_filter(dataset: Dataset) -> List[str]:
    """Render sub-product filter checkboxes and return selected options."""
    selected = []
    if dataset.sub_filters:
        st.sidebar.markdown("**📋 Sub-Product**")
        for option in dataset.sub_filters.options:
            if st.sidebar.checkbox(option, value=True, key=f"sub_{option}"):
                selected.append(option)
    return selected


def render_population_filter(dataset: Dataset) -> bool:
    """Render population filter checkbox and return value."""
    if dataset.population_filter:
        st.sidebar.markdown("**👥 Population**")
        return st.sidebar.checkbox("Hide Sectorial", value=True, key="hide_sectorial")
    return False


def render_period_selector(periods: List[int]) -> int:
    """Render period selector and return selected period."""
    st.sidebar.markdown("---")
    st.sidebar.header("🔧 Filters")
    
    return st.sidebar.selectbox(
        "📅 Report Period",
        options=periods,
        index=0,
        format_func=format_period
    )


def render_classification_filter(df: pd.DataFrame) -> str:
    """Render classification filter and return selection."""
    if 'FUND_CLASSIFICATION' in df.columns:
        classifications = ['All'] + sorted(df['FUND_CLASSIFICATION'].unique().tolist())
        return st.sidebar.selectbox(
            "📁 Fund Classification",
            options=classifications
        )
    return 'All'


def render_company_filter(df: pd.DataFrame) -> str:
    """Render company filter and return selection."""
    corp_col = None
    if 'MANAGING_CORPORATION' in df.columns:
        corp_col = 'MANAGING_CORPORATION'
    elif 'PARENT_COMPANY_NAME' in df.columns:
        corp_col = 'PARENT_COMPANY_NAME'
    
    if corp_col:
        corporations = ['All'] + sorted(df[corp_col].dropna().unique().tolist())
        selected = st.sidebar.selectbox("🏢 Company", options=corporations)
        return selected, corp_col
    return 'All', None


def render_assets_filter(df: pd.DataFrame) -> float:
    """Render minimum assets filter and return value."""
    if 'TOTAL_ASSETS' in df.columns:
        max_assets = float(df['TOTAL_ASSETS'].max()) if df['TOTAL_ASSETS'].notna().any() else 10000.0
        return st.sidebar.slider(
            "💰 Minimum Total Assets (M)",
            min_value=0.0,
            max_value=min(max_assets, 10000.0),
            value=0.0,
            step=10.0
        )
    return 0.0


def render_exposure_filters(df: pd.DataFrame) -> Tuple[Tuple[float, float], ...]:
    """Render exposure filters and return ranges."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📈 Exposure Filters**")
    
    stock_range = st.sidebar.slider(
        "📊 Stock Market Exposure (%)",
        min_value=0.0,
        max_value=100.0,
        value=(0.0, 100.0),
        step=1.0
    )
    
    foreign_range = st.sidebar.slider(
        "🌍 Foreign Exposure (%)",
        min_value=0.0,
        max_value=100.0,
        value=(0.0, 100.0),
        step=1.0
    )
    
    currency_range = st.sidebar.slider(
        "💱 Foreign Currency Exposure (%)",
        min_value=0.0,
        max_value=100.0,
        value=(0.0, 100.0),
        step=1.0
    )
    
    return stock_range, foreign_range, currency_range


def render_search_filter() -> str:
    """Render fund name search and return search term."""
    return st.sidebar.text_input("🔍 Search Fund Name", "")


def render_cache_info(cache_age: Optional[float]) -> None:
    """Render cache information."""
    if cache_age is not None:
        st.sidebar.caption(f"📦 Cache: {cache_age:.1f}h old")


def render_refresh_button() -> bool:
    """Render refresh data button and return if clicked."""
    return st.sidebar.button("🔄 Refresh Data")

