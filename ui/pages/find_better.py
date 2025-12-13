"""
Find Better page - Find better funds based on user's current fund.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, Optional

from config.settings import COLORS, COLUMN_LABELS
from services.find_better_service import FindBetterService


# Yield period options
YIELD_PERIODS = {
    '3M': 3,
    '6M': 6,
    '1Y': 12,
    '3Y': 36,
    '5Y': 60
}


def render_find_better(
    all_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
    selected_period: int,
    find_better_service: FindBetterService,
    dataset_registry: Optional[Dict[str, Any]] = None,
    data_service = None,
    current_dataset_key: Optional[str] = None
) -> None:
    """Render the Find Better tab."""
    
    st.subheader("🔍 Find Better Funds")
    st.caption("Find funds that outperform your current fund with similar or unrestricted strategy")
    
    # --- Step 0: Product Selection (if registry available) ---
    working_all_df = all_df
    working_filtered_df = filtered_df
    working_period = selected_period
    
    if dataset_registry and data_service:
        st.markdown("### 📦 Select Product")
        
        # Product options
        product_options = {key: cfg.get('name', key) for key, cfg in dataset_registry.items()}
        product_keys = list(product_options.keys())
        product_labels = [product_options[k] for k in product_keys]
        
        col_prod = st.columns([2, 2, 2])
        
        with col_prod[0]:
            # Find current index
            current_idx = product_keys.index(current_dataset_key) if current_dataset_key in product_keys else 0
            selected_product_key = st.selectbox(
                "📊 Product",
                options=product_keys,
                format_func=lambda x: product_options[x],
                index=current_idx,
                key="fb_product"
            )
        
        # Get dataset config
        dataset_config = dataset_registry.get(selected_product_key, {})
        
        # Sub-product filter
        with col_prod[1]:
            sub_filters = dataset_config.get('sub_filters')
            selected_sub_products = None
            if sub_filters:
                sub_col = sub_filters.get('column', 'FUND_CLASSIFICATION')
                sub_options = sub_filters.get('options', [])
                if sub_options:
                    selected_sub_products = st.multiselect(
                        "📁 Sub-Product",
                        options=sub_options,
                        default=sub_options,
                        key="fb_sub_product"
                    )
        
        with col_prod[2]:
            # Yield period selection
            yield_period = st.selectbox(
                "📅 Comparison Period",
                options=list(YIELD_PERIODS.keys()),
                index=2,  # Default to 1Y
                key="find_better_period"
            )
            period_months = YIELD_PERIODS[yield_period]
        
        # Load data for selected product if different
        if selected_product_key != current_dataset_key:
            with st.spinner(f"Loading {product_options[selected_product_key]} data..."):
                working_all_df = data_service.load_data(selected_product_key)
                if working_all_df is None or working_all_df.empty:
                    st.error(f"Failed to load data for {product_options[selected_product_key]}")
                    return
                
                # Get available periods
                if 'REPORT_PERIOD' in working_all_df.columns:
                    periods = sorted(working_all_df['REPORT_PERIOD'].unique(), reverse=True)
                    if periods:
                        working_period = periods[0]
                        working_filtered_df = working_all_df[working_all_df['REPORT_PERIOD'] == working_period]
        
        # Apply sub-product filter
        if selected_sub_products and sub_filters:
            sub_col = sub_filters.get('column', 'FUND_CLASSIFICATION')
            if sub_col in working_filtered_df.columns:
                working_filtered_df = working_filtered_df[working_filtered_df[sub_col].isin(selected_sub_products)]
                working_all_df = working_all_df[working_all_df[sub_col].isin(selected_sub_products)]
        
        st.markdown("---")
    else:
        # Original behavior - period selection only
        yield_period = st.selectbox(
            "📅 Comparison Period",
            options=list(YIELD_PERIODS.keys()),
            index=2,
            key="find_better_period"
        )
        period_months = YIELD_PERIODS[yield_period]
    
    # --- Step 1: Fund Selection ---
    st.markdown("### 1️⃣ Select Your Current Fund")
    
    # Filter options to narrow down fund search
    working_df = working_filtered_df.copy()
    
    col_filters = st.columns(2)
    
    with col_filters[0]:
        # Company filter
        corp_col = 'MANAGING_CORPORATION' if 'MANAGING_CORPORATION' in working_df.columns else 'PARENT_COMPANY_NAME'
        if corp_col in working_df.columns:
            companies = ['All'] + sorted(working_df[corp_col].dropna().unique().tolist())
            selected_company = st.selectbox("🏢 Company", companies, key="fb_company")
            if selected_company != 'All':
                working_df = working_df[working_df[corp_col] == selected_company]
    
    with col_filters[1]:
        # Classification filter
        if 'FUND_CLASSIFICATION' in working_df.columns:
            classifications = ['All'] + sorted(working_df['FUND_CLASSIFICATION'].dropna().unique().tolist())
            selected_class = st.selectbox("📁 Classification", classifications, key="fb_class")
            if selected_class != 'All':
                working_df = working_df[working_df['FUND_CLASSIFICATION'] == selected_class]
    
    # Fund selection
    fund_options = working_df[['FUND_ID', 'FUND_NAME']].drop_duplicates()
    fund_id_to_name = dict(zip(fund_options['FUND_ID'], fund_options['FUND_NAME']))
    fund_ids = sorted(fund_options['FUND_ID'].tolist())
    
    if not fund_ids:
        st.warning("No funds match the selected filters. Try adjusting Company or Classification.")
        return
    
    selected_fund_id = st.selectbox(
        f"🔍 Select Fund ({len(fund_ids)} available)",
        options=fund_ids,
        format_func=lambda x: f"{x} - {fund_id_to_name.get(x, '')[:50]}",
        key="find_better_fund_select"
    )
    
    # Get user's fund data
    user_fund_df = working_filtered_df[working_filtered_df['FUND_ID'] == selected_fund_id]
    
    if user_fund_df.empty:
        st.error("Could not find fund data. Please try another fund.")
        return
    
    user_fund = user_fund_df.iloc[0]
    
    # Calculate user's yield for selected period
    user_yield = find_better_service.calculate_period_yield(
        working_all_df, selected_fund_id, period_months, working_period
    )
    
    # Show user's fund info
    st.markdown("---")
    st.markdown("### 📋 Your Fund")
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1:
        st.metric("Fund ID", selected_fund_id)
    with col2:
        if user_yield is not None:
            st.metric(f"{yield_period} Yield", f"{user_yield:.2f}%")
        else:
            st.metric(f"{yield_period} Yield", "N/A")
    with col3:
        std = user_fund.get('STANDARD_DEVIATION')
        st.metric("Std Dev", f"{std:.2f}" if std else "N/A")
    with col4:
        stock_exp = user_fund.get('STOCK_MARKET_EXPOSURE')
        st.metric("Stock %", f"{stock_exp:.1f}%" if stock_exp else "N/A")
    with col5:
        foreign_exp = user_fund.get('FOREIGN_EXPOSURE')
        st.metric("Foreign %", f"{foreign_exp:.1f}%" if foreign_exp else "N/A")
    with col6:
        currency_exp = user_fund.get('FOREIGN_CURRENCY_EXPOSURE')
        st.metric("Currency %", f"{currency_exp:.1f}%" if currency_exp else "N/A")
    with col7:
        liquid = user_fund.get('LIQUID_ASSETS_PERCENT')
        st.metric("Liquid %", f"{liquid:.1f}%" if liquid else "N/A")
    
    st.caption(f"**{user_fund.get('FUND_NAME', 'Unknown')}**")
    
    if user_yield is None:
        st.error(f"Insufficient data for {yield_period} yield calculation. Try a shorter period.")
        return
    
    # --- Step 2: Find Better Funds ---
    st.markdown("---")
    st.markdown("### 2️⃣ Better Fund Options")
    
    # Get eligible funds
    with st.spinner("Searching for better funds..."):
        eligible_df = find_better_service.get_eligible_funds(
            working_all_df, user_fund, period_months, working_period
        )
    
    if eligible_df.empty:
        st.info("No eligible funds found for comparison.")
        return
    
    # Find unrestricted better funds
    unrestricted_df = find_better_service.find_unrestricted_better(
        eligible_df, user_fund, user_yield, top_n=5
    )
    
    # Find similar strategy better funds
    similar_df = find_better_service.find_similar_strategy_better(
        eligible_df, user_fund, user_yield, top_n=5
    )
    
    # Display results in two columns
    col_unrestricted, col_similar = st.columns(2)
    
    with col_unrestricted:
        st.markdown("#### 🚀 Unrestricted Strategy")
        st.caption("Better yield, similar risk, any exposure")
        
        if unrestricted_df.empty:
            st.info("🎉 Your fund is already optimal! No funds found with better yield AND acceptable risk level. Consider adjusting thresholds in Settings.")
            selected_unrestricted = None
        else:
            display_cols = ['FUND_ID', 'FUND_NAME', 'CALC_YIELD', 'STANDARD_DEVIATION', 
                          'STOCK_MARKET_EXPOSURE', 'FOREIGN_EXPOSURE', 'FOREIGN_CURRENCY_EXPOSURE', 'LIQUID_ASSETS_PERCENT']
            display_df = unrestricted_df[
                [c for c in display_cols if c in unrestricted_df.columns]
            ].copy()
            
            # Rename columns
            col_rename = {
                'FUND_ID': 'ID', 
                'FUND_NAME': 'Fund Name', 
                'CALC_YIELD': f'{yield_period} Yield (%)', 
                'STANDARD_DEVIATION': 'Std Dev',
                'STOCK_MARKET_EXPOSURE': 'Stock %',
                'FOREIGN_EXPOSURE': 'Foreign %',
                'FOREIGN_CURRENCY_EXPOSURE': 'Currency %',
                'LIQUID_ASSETS_PERCENT': 'Liquid %'
            }
            display_df = display_df.rename(columns=col_rename)
            
            # Round numeric columns
            for col in [f'{yield_period} Yield (%)', 'Std Dev', 'Stock %', 'Foreign %', 'Currency %', 'Liquid %']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].round(1)
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Selection for comparison
            unrestricted_ids = unrestricted_df['FUND_ID'].tolist()
            selected_unrestricted = st.selectbox(
                "Select for comparison",
                options=[None] + unrestricted_ids,
                format_func=lambda x: "-- Choose --" if x is None else f"{x}",
                key="select_unrestricted"
            )
    
    with col_similar:
        st.markdown("#### 🎯 Similar Strategy")
        st.caption("Better yield, similar risk & exposures")
        
        if similar_df.empty:
            st.info("🎉 No funds with matching strategy perform better. Your fund is well-positioned!")
            selected_similar = None
        else:
            display_cols = ['FUND_ID', 'FUND_NAME', 'CALC_YIELD', 'STANDARD_DEVIATION',
                          'STOCK_MARKET_EXPOSURE', 'FOREIGN_EXPOSURE', 'FOREIGN_CURRENCY_EXPOSURE', 'LIQUID_ASSETS_PERCENT']
            display_df = similar_df[
                [c for c in display_cols if c in similar_df.columns]
            ].copy()
            
            # Rename columns
            col_rename = {
                'FUND_ID': 'ID', 
                'FUND_NAME': 'Fund Name', 
                'CALC_YIELD': f'{yield_period} Yield (%)', 
                'STANDARD_DEVIATION': 'Std Dev',
                'STOCK_MARKET_EXPOSURE': 'Stock %',
                'FOREIGN_EXPOSURE': 'Foreign %',
                'FOREIGN_CURRENCY_EXPOSURE': 'Currency %',
                'LIQUID_ASSETS_PERCENT': 'Liquid %'
            }
            display_df = display_df.rename(columns=col_rename)
            
            # Round numeric columns
            for col in [f'{yield_period} Yield (%)', 'Std Dev', 'Stock %', 'Foreign %', 'Currency %', 'Liquid %']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].round(1)
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Selection for comparison
            similar_ids = similar_df['FUND_ID'].tolist()
            selected_similar = st.selectbox(
                "Select for comparison",
                options=[None] + similar_ids,
                format_func=lambda x: "-- Choose --" if x is None else f"{x}",
                key="select_similar"
            )
    
    # --- Step 3: Comparison ---
    selected_for_comparison = selected_unrestricted or selected_similar
    
    if selected_for_comparison:
        st.markdown("---")
        st.markdown("### 3️⃣ Comparison")
        
        # Get comparison fund data
        compare_fund_df = working_filtered_df[working_filtered_df['FUND_ID'] == selected_for_comparison]
        if compare_fund_df.empty:
            compare_fund_df = working_all_df[
                (working_all_df['FUND_ID'] == selected_for_comparison) & 
                (working_all_df['REPORT_PERIOD'] == working_period)
            ]
        
        if compare_fund_df.empty:
            st.error("Could not load comparison fund data")
            return
        
        compare_fund = compare_fund_df.iloc[0]
        compare_yield = find_better_service.calculate_period_yield(
            working_all_df, selected_for_comparison, period_months, working_period
        )
        
        # Create comparison visualization
        render_comparison_chart(
            user_fund, compare_fund,
            user_yield, compare_yield,
            yield_period, working_all_df, working_period
        )
        
        # Summary
        render_comparison_summary(
            user_fund, compare_fund,
            user_yield, compare_yield,
            yield_period
        )


def render_comparison_chart(
    user_fund: pd.Series,
    compare_fund: pd.Series,
    user_yield: float,
    compare_yield: float,
    yield_period: str,
    all_df: pd.DataFrame,
    selected_period: int
) -> None:
    """Render comparison charts."""
    
    user_name = str(user_fund.get('FUND_NAME', 'Your Fund'))[:25]
    compare_name = str(compare_fund.get('FUND_NAME', 'Better Fund'))[:25]
    
    # Create subplot
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Yield & Risk", "Exposures"),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Yield & Risk comparison
    metrics = [f'{yield_period} Yield (%)', 'Std Dev']
    user_values = [user_yield or 0, user_fund.get('STANDARD_DEVIATION', 0)]
    compare_values = [compare_yield or 0, compare_fund.get('STANDARD_DEVIATION', 0)]
    
    fig.add_trace(
        go.Bar(name=user_name, x=metrics, y=user_values, marker_color=COLORS[0]),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(name=compare_name, x=metrics, y=compare_values, marker_color=COLORS[1]),
        row=1, col=1
    )
    
    # Exposures comparison
    exposure_metrics = ['Stock %', 'Foreign %', 'Currency %', 'Liquid %']
    user_exposures = [
        user_fund.get('STOCK_MARKET_EXPOSURE', 0),
        user_fund.get('FOREIGN_EXPOSURE', 0),
        user_fund.get('FOREIGN_CURRENCY_EXPOSURE', 0),
        user_fund.get('LIQUID_ASSETS_PERCENT', 0)
    ]
    compare_exposures = [
        compare_fund.get('STOCK_MARKET_EXPOSURE', 0),
        compare_fund.get('FOREIGN_EXPOSURE', 0),
        compare_fund.get('FOREIGN_CURRENCY_EXPOSURE', 0),
        compare_fund.get('LIQUID_ASSETS_PERCENT', 0)
    ]
    
    fig.add_trace(
        go.Bar(name=user_name, x=exposure_metrics, y=user_exposures, 
               marker_color=COLORS[0], showlegend=False),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(name=compare_name, x=exposure_metrics, y=compare_exposures,
               marker_color=COLORS[1], showlegend=False),
        row=1, col=2
    )
    
    fig.update_layout(
        height=350,
        barmode='group',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_comparison_summary(
    user_fund: pd.Series,
    compare_fund: pd.Series,
    user_yield: float,
    compare_yield: float,
    yield_period: str
) -> None:
    """Render comparison summary text."""
    
    user_name = user_fund.get('FUND_NAME', 'Your Fund')
    compare_name = compare_fund.get('FUND_NAME', 'Recommended Fund')
    
    yield_diff = (compare_yield or 0) - (user_yield or 0)
    std_diff = (user_fund.get('STANDARD_DEVIATION', 0)) - (compare_fund.get('STANDARD_DEVIATION', 0))
    
    st.markdown("#### 📊 Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        delta_color = "normal" if yield_diff > 0 else "inverse"
        st.metric(
            f"{yield_period} Yield Improvement",
            f"+{yield_diff:.2f}%" if yield_diff > 0 else f"{yield_diff:.2f}%",
            delta=f"{yield_diff:.2f}%",
            delta_color=delta_color
        )
    
    with col2:
        delta_color = "normal" if std_diff > 0 else "inverse"
        st.metric(
            "Risk Reduction",
            f"{std_diff:.2f}",
            delta=f"{std_diff:.2f}",
            delta_color=delta_color
        )
    
    with col3:
        fee_diff = (user_fund.get('AVG_ANNUAL_MANAGEMENT_FEE', 0)) - (compare_fund.get('AVG_ANNUAL_MANAGEMENT_FEE', 0))
        st.metric(
            "Fee Savings",
            f"{fee_diff:.2f}%",
            delta=f"{fee_diff:.2f}%",
            delta_color="normal" if fee_diff > 0 else "inverse"
        )
    
    # Text summary
    if yield_diff > 0:
        st.success(f"""
        **Recommendation:** Consider switching from **{user_name[:30]}** to **{compare_name[:30]}**.
        
        - 📈 **{yield_diff:.2f}%** higher average {yield_period} yield
        - 📉 **{std_diff:.2f}** {'lower' if std_diff > 0 else 'higher'} standard deviation
        - 💰 **{fee_diff:.2f}%** {'lower' if fee_diff > 0 else 'higher'} management fees
        """)
    else:
        st.info("The selected fund doesn't show significant improvement over your current fund.")

