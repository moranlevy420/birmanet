"""
Find Better page - Find better funds based on user's current fund.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    find_better_service: FindBetterService
) -> None:
    """Render the Find Better tab."""
    
    st.subheader("🔍 Find Better Funds")
    st.caption("Find funds that outperform your current fund with similar or unrestricted strategy")
    
    # --- Step 1: Fund Selection ---
    st.markdown("### 1️⃣ Select Your Current Fund")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get unique funds from filtered data
        fund_options = filtered_df[['FUND_ID', 'FUND_NAME']].drop_duplicates()
        fund_id_to_name = dict(zip(fund_options['FUND_ID'], fund_options['FUND_NAME']))
        fund_ids = sorted(fund_options['FUND_ID'].tolist())
        
        if not fund_ids:
            st.warning("No funds available. Adjust your filters in the sidebar.")
            return
        
        selected_fund_id = st.selectbox(
            "Select by Fund ID",
            options=fund_ids,
            format_func=lambda x: f"{x} - {fund_id_to_name.get(x, '')[:40]}",
            key="find_better_fund_select"
        )
    
    with col2:
        # Yield period selection
        yield_period = st.selectbox(
            "Comparison Period",
            options=list(YIELD_PERIODS.keys()),
            index=2,  # Default to 1Y
            key="find_better_period"
        )
        period_months = YIELD_PERIODS[yield_period]
    
    # Get user's fund data
    user_fund_df = filtered_df[filtered_df['FUND_ID'] == selected_fund_id]
    
    if user_fund_df.empty:
        st.error("Could not find fund data. Please try another fund.")
        return
    
    user_fund = user_fund_df.iloc[0]
    
    # Calculate user's yield for selected period
    user_yield = find_better_service.calculate_period_yield(
        all_df, selected_fund_id, period_months, selected_period
    )
    
    # Show user's fund info
    st.markdown("---")
    st.markdown("### 📋 Your Fund")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fund ID", selected_fund_id)
    with col2:
        if user_yield is not None:
            st.metric(f"{yield_period} Avg Yield", f"{user_yield:.2f}%")
        else:
            st.metric(f"{yield_period} Avg Yield", "N/A")
    with col3:
        std = user_fund.get('STANDARD_DEVIATION')
        st.metric("Std Dev", f"{std:.2f}" if std else "N/A")
    with col4:
        stock_exp = user_fund.get('STOCK_MARKET_EXPOSURE')
        st.metric("Stock Exposure", f"{stock_exp:.1f}%" if stock_exp else "N/A")
    
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
            all_df, user_fund, period_months, selected_period
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
            display_cols = ['FUND_ID', 'FUND_NAME', 'CALC_YIELD', 'STANDARD_DEVIATION']
            display_df = unrestricted_df[
                [c for c in display_cols if c in unrestricted_df.columns]
            ].copy()
            display_df.columns = ['ID', 'Fund Name', f'{yield_period} Yield (%)', 'Std Dev']
            display_df[f'{yield_period} Yield (%)'] = display_df[f'{yield_period} Yield (%)'].round(2)
            display_df['Std Dev'] = display_df['Std Dev'].round(2)
            
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
            display_cols = ['FUND_ID', 'FUND_NAME', 'CALC_YIELD', 'STANDARD_DEVIATION']
            display_df = similar_df[
                [c for c in display_cols if c in similar_df.columns]
            ].copy()
            display_df.columns = ['ID', 'Fund Name', f'{yield_period} Yield (%)', 'Std Dev']
            display_df[f'{yield_period} Yield (%)'] = display_df[f'{yield_period} Yield (%)'].round(2)
            display_df['Std Dev'] = display_df['Std Dev'].round(2)
            
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
        compare_fund_df = filtered_df[filtered_df['FUND_ID'] == selected_for_comparison]
        if compare_fund_df.empty:
            compare_fund_df = all_df[
                (all_df['FUND_ID'] == selected_for_comparison) & 
                (all_df['REPORT_PERIOD'] == selected_period)
            ]
        
        if compare_fund_df.empty:
            st.error("Could not load comparison fund data")
            return
        
        compare_fund = compare_fund_df.iloc[0]
        compare_yield = find_better_service.calculate_period_yield(
            all_df, selected_for_comparison, period_months, selected_period
        )
        
        # Create comparison visualization
        render_comparison_chart(
            user_fund, compare_fund,
            user_yield, compare_yield,
            yield_period, all_df, selected_period
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

