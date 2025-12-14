"""
About page - application information.
"""

import streamlit as st
from datetime import datetime

from config.settings import VERSION


def render_about() -> None:
    """Render the About tab."""
    st.subheader("ℹ️ About Find Better")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        **Current Version:** `v{VERSION}`
        
        Find Better is an interactive dashboard for exploring Israeli pension fund data 
        from [data.gov.il](https://data.gov.il).
        
        **Data Sources:**
        - 🏦 Pension Funds (קרנות פנסיה)
        - 💰 Kupot Gemel (קופות גמל)
        - 📚 Hishtalmut (קרנות השתלמות)
        - 📈 Investment Gemel (קופות גמל להשקעה)
        - 🛡️ Insurance Funds (ביטוח מנהלים)
        """)
    
    with col2:
        st.metric("Version", f"v{VERSION}")
        st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d')}")
    
    st.markdown("---")
    
    # Version History
    st.markdown("### 📜 Version History")
    
    versions = [
        {
            "version": "2.4.0",
            "date": "Dec 2024",
            "title": "Compounded Yield Calculation",
            "features": [
                "📊 Fixed 1Y Avg Yield to use compounded returns",
                "🔢 Proper annualization formula: (1+r₁)×(1+r₂)×...×(1+rₙ)^(12/n)",
                "📈 Find Better now uses compounded yields for all periods",
                "✅ Added unit tests for yield calculations"
            ]
        },
        {
            "version": "2.3.0",
            "date": "Dec 2024",
            "title": "Private Repository & Migration Fixes",
            "features": [
                "🔒 Private repository distribution support",
                "🔑 GitHub token authentication for updates",
                "📦 One-click release creation script",
                "🗄️ Legacy database migration fix",
                "🔐 Clear password display on setup",
                "📋 Improved Windows install/update scripts"
            ]
        },
        {
            "version": "2.2.1",
            "date": "Dec 2024",
            "title": "Find Better Enhancements",
            "features": [
                "🏢 Company filter in Find Better",
                "📁 Classification filter in Find Better",
                "📊 Exposure columns in result tables",
                "💧 Liquidity % added to comparisons",
                "🔑 Password reset improvements"
            ]
        },
        {
            "version": "2.2.0",
            "date": "Dec 2024",
            "title": "Find Better Feature",
            "features": [
                "🔍 Find Better tab - find outperforming funds",
                "🎯 Similar Strategy - funds with matching exposures",
                "🚀 Unrestricted Strategy - any exposure level",
                "⚙️ Admin configurable thresholds",
                "📊 Visual comparison with charts",
                "📈 3M/6M/1Y/3Y/5Y yield period selection"
            ]
        },
        {
            "version": "2.1.3",
            "date": "Dec 2024",
            "title": "Version History",
            "features": [
                "📜 Full version history in About tab",
                "✨ Expandable changelog with features",
                "🎯 Current version highlighted"
            ]
        },
        {
            "version": "2.1.2",
            "date": "Dec 2024",
            "title": "Persistent Login",
            "features": [
                "🔐 Remember Me - stay logged in for 30 days",
                "🍪 Secure session cookies",
                "🚪 Proper logout invalidation"
            ]
        },
        {
            "version": "2.1.0",
            "date": "Dec 2024", 
            "title": "User Authentication",
            "features": [
                "👤 Admin & Member roles",
                "🔑 Secure bcrypt password hashing",
                "⚙️ Admin Settings tab for user management",
                "🔄 Force password change on first login"
            ]
        },
        {
            "version": "2.0.3",
            "date": "Dec 2024",
            "title": "1Y Trailing Yield",
            "features": [
                "📊 New 1Y Avg Yield column (TTM)",
                "📋 Default sort by 1Y yield",
                "🔢 Calculated from 12-month historical data"
            ]
        },
        {
            "version": "2.0.0",
            "date": "Dec 2024",
            "title": "Major Refactoring",
            "features": [
                "🏗️ Modular architecture (services, models, UI)",
                "📁 JSON-based dataset configuration",
                "🗄️ SQLAlchemy + Alembic for database",
                "☁️ Cloud-ready architecture"
            ]
        },
        {
            "version": "1.3.0",
            "date": "Dec 2024",
            "title": "Auto-Update",
            "features": [
                "🔄 In-app GitHub update checker",
                "⬇️ One-click update download",
                "📦 Automatic file replacement"
            ]
        },
        {
            "version": "1.2.0",
            "date": "Dec 2024",
            "title": "Multi-Product Support",
            "features": [
                "🏦 Split Gemel into 3 product types",
                "👥 Population filter (Hide Sectorial)",
                "🛡️ Added Insurance funds dataset",
                "📋 Sub-product multi-select filters"
            ]
        },
        {
            "version": "1.1.0",
            "date": "Dec 2024",
            "title": "Enhanced UI & Features",
            "features": [
                "📊 AgGrid interactive tables",
                "📌 Frozen Fund ID & Name columns",
                "🔀 Click column headers to sort",
                "📈 Dynamic Top 5 chart updates",
                "💾 Disk caching with SQLite"
            ]
        },
        {
            "version": "1.0.0",
            "date": "Dec 2024",
            "title": "Initial Release",
            "features": [
                "📋 World View data table",
                "📊 Charts & visualizations",
                "⚖️ Fund comparison",
                "📈 Historical trends",
                "🔍 Filters & search",
                "📥 CSV export"
            ]
        }
    ]
    
    for v in versions:
        with st.expander(f"**v{v['version']}** - {v['title']} ({v['date']})", expanded=(v['version'] == VERSION)):
            for feature in v['features']:
                st.markdown(f"- {feature}")
    
    st.markdown("---")
    st.caption("Made with ❤️ for better pension decisions")


def render_under_construction(title: str, description: str) -> None:
    """Render an under construction page."""
    st.subheader(title)
    st.info("🚧 Under Construction - Coming Soon!")
    st.markdown(f"*{description}*")

