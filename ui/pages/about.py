"""
About page - application information.
"""

import streamlit as st
from datetime import datetime

from config.settings import VERSION


def render_about() -> None:
    """Render the About tab."""
    st.subheader("ℹ️ About Find Better")
    
    st.markdown(f"""
    **Version:** {VERSION}
    
    **What is Find Better?**
    
    Find Better is an interactive dashboard for exploring Israeli pension fund data 
    from [data.gov.il](https://data.gov.il).
    
    **Features:**
    - 📋 View and filter fund data
    - 📊 Interactive charts and visualizations
    - ⚖️ Compare multiple funds side-by-side
    - 📈 Historical performance analysis
    - 🔄 Auto-update from GitHub
    
    **Data Sources:**
    - Pension Funds (קרנות פנסיה)
    - Kupot Gemel (קופות גמל)
    - Hishtalmut (קרנות השתלמות)
    - Investment Gemel (קופות גמל להשקעה)
    - Insurance Funds (ביטוח מנהלים)
    
    ---
    
    **Architecture:**
    - Modular design with separated concerns
    - Service layer for data and caching
    - Configurable via JSON files
    - Cloud-ready with swappable cache backends
    
    ---
    
    **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """)


def render_under_construction(title: str, description: str) -> None:
    """Render an under construction page."""
    st.subheader(title)
    st.info("🚧 Under Construction - Coming Soon!")
    st.markdown(f"*{description}*")

