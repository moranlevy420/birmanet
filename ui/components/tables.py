"""
Table components using AgGrid.
"""

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode, ColumnsAutoSizeMode
from typing import List, Optional, Tuple

from config.settings import DISPLAY_COLUMNS, COLUMN_LABELS, COLUMN_GROUPS, COLUMN_GROUP_COLORS


def get_column_group(col_name: str) -> str:
    """Get the group name for a column."""
    for group, cols in COLUMN_GROUPS.items():
        if col_name in cols:
            return group
    return 'Other'


def get_header_style(group: str) -> dict:
    """Get header style for a column group."""
    color = COLUMN_GROUP_COLORS.get(group, '#3a3a3a')
    return {
        'backgroundColor': color,
        'color': 'white',
        'fontWeight': 'bold'
    }


def create_fund_table(
    df: pd.DataFrame,
    height: int = 280,
    key: str = "fund_table",
    filter_hash: str = "",
    sort_column: str = "YTD (%)",
    sort_ascending: bool = False
) -> Tuple[pd.DataFrame, dict]:
    """
    Create an interactive fund data table using AgGrid.
    
    Args:
        df: DataFrame with fund data
        height: Table height in pixels
        key: Unique key for the table component
        filter_hash: Hash to track filter changes
        sort_column: Column to sort by
        sort_ascending: Sort direction
        
    Returns:
        Tuple of (sorted_dataframe, grid_response)
    """
    # Prepare display dataframe
    available_cols = [c for c in DISPLAY_COLUMNS if c in df.columns]
    display_df = df[available_cols].copy()
    display_df = display_df.rename(columns=COLUMN_LABELS)
    
    # Pre-sort by the specified column
    if sort_column in display_df.columns:
        display_df = display_df.sort_values(
            by=sort_column, 
            ascending=sort_ascending, 
            na_position='last'
        )
    elif 'YTD (%)' in display_df.columns:
        display_df = display_df.sort_values(
            by='YTD (%)', 
            ascending=False, 
            na_position='last'
        )
    display_df = display_df.reset_index(drop=True)
    
    # Configure AgGrid - simple config
    gb = GridOptionsBuilder.from_dataframe(display_df)
    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        wrapHeaderText=True,
        autoHeaderHeight=True,
        sortingOrder=['desc', 'asc', None]
    )
    
    # Column tooltips - show full description on hover
    column_tooltips = {
        'Fund ID': 'Unique fund identifier',
        'Fund Name': 'Fund name (Hebrew)',
        '1M (%)': 'Monthly yield percentage',
        'YTD (%)': 'Year-to-date yield percentage',
        '1Y (%)': 'Trailing 1-year yield percentage',
        '3Y (%)': 'Average annual yield over 3 years',
        '5Y (%)': 'Average annual yield over 5 years',
        'Sharpe': 'Sharpe ratio (risk-adjusted return)',
        'Std Dev': 'Standard deviation (volatility)',
        'Assets (M)': 'Total assets under management (millions)',
        'Stocks %': 'Stock market exposure percentage',
        'Foreign %': 'Foreign assets exposure percentage',
        'Currency %': 'Foreign currency exposure percentage',
        'Liquid %': 'Liquid assets percentage',
        'Mgmt %': 'Annual management fee percentage',
        'Deposit %': 'Deposit fee percentage',
        'Classification': 'Fund classification/type',
        'Alpha': 'Alpha (excess return vs benchmark)',
        'Net Deposits': 'Net monthly deposits (millions)',
        'Inception': 'Fund inception date',
    }
    
    # Configure all columns with tooltips - let grid handle widths naturally
    for col in display_df.columns:
        tooltip = column_tooltips.get(col, col)
        
        if col == 'Fund Name':
            gb.configure_column(col, width=200, wrapHeaderText=False,
                                cellStyle={'direction': 'rtl', 'textAlign': 'right'}, headerTooltip=tooltip)
        elif col == 'Classification':
            gb.configure_column(col, width=110,
                                cellStyle={'direction': 'rtl', 'textAlign': 'right'}, headerTooltip=tooltip)
        else:
            gb.configure_column(col, headerTooltip=tooltip)
    
    # Configure initial sort - show arrow on default sorted column
    if sort_column in display_df.columns:
        gb.configure_column(sort_column, sort='desc' if not sort_ascending else 'asc')
    
    # Apply header classes based on column groups (BEFORE gb.build())
    for col in display_df.columns:
        # Find the original column name
        orig_col = None
        for k, v in COLUMN_LABELS.items():
            if v == col:
                orig_col = k
                break
        if orig_col:
            group = get_column_group(orig_col)
            header_class = f'header-{group.lower().replace(" & ", "-").replace(" ", "-")}'
            gb.configure_column(col, headerClass=header_class)
    
    # Enable column moving and text selection
    gb.configure_grid_options(
        suppressDragLeaveHidesColumns=True,
        enableCellTextSelection=True,
        ensureDomOrder=True
    )
    
    grid_options = gb.build()
    
    # Column group colored headers (like v2.6.0)
    custom_css = {
        # Root wrapper - light background
        '.ag-root-wrapper': {
            'background-color': '#ffffff !important',
        },
        '.ag-body-viewport': {
            'background-color': '#ffffff !important',
        },
        # Column group header colors
        '.header-identifiers': {
            'background-color': '#1e3a5f !important',  # Dark blue
            'color': 'white !important',
        },
        '.header-risk-return': {
            'background-color': '#1e5631 !important',  # Dark green
            'color': 'white !important',
        },
        '.header-exposure': {
            'background-color': '#4a1e5f !important',  # Dark purple
            'color': 'white !important',
        },
        '.header-fees': {
            'background-color': '#5f3a1e !important',  # Dark orange/brown
            'color': 'white !important',
        },
        '.header-other': {
            'background-color': '#3a3a3a !important',  # Dark gray
            'color': 'white !important',
        },
        # Header cell styling
        '.ag-header-cell': {
            'border-right': '2px solid white !important',
        },
        '.ag-header-cell-label': {
            'color': 'white !important',
        },
        # Light table body with dark text
        '.ag-row': {
            'background-color': '#ffffff !important',
            'color': '#1e293b !important',
        },
        '.ag-row-odd': {
            'background-color': '#f1f5f9 !important',
            'color': '#1e293b !important',
        },
        '.ag-row-even': {
            'background-color': '#ffffff !important',
            'color': '#1e293b !important',
        },
        '.ag-cell': {
            'border-right': '1px solid #e2e8f0 !important',
            'color': '#1e293b !important',
        },
        # Sort icons - make visible
        '.ag-icon-asc, .ag-icon-desc': {
            'color': 'white !important',
            'opacity': '1 !important',
        },
        '.ag-sort-indicator-icon': {
            'color': 'white !important',
            'opacity': '1 !important',
        },
        '.ag-header-icon': {
            'color': 'white !important',
            'opacity': '1 !important',
        },
    }
    
    # Simple grid - no auto-sizing, stable key
    grid_response = AgGrid(
        display_df,
        gridOptions=grid_options,
        height=height,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        theme="alpine",
        allow_unsafe_jscode=True,
        custom_css=custom_css,
        key=key
    )
    
    # Get sorted data from grid
    sorted_df = pd.DataFrame(grid_response['data']) if grid_response['data'] is not None else display_df
    
    return sorted_df, grid_response


def create_comparison_table(
    df: pd.DataFrame,
    selected_funds: List[str],
    fund_dict: dict
) -> pd.DataFrame:
    """
    Create a comparison table for selected funds.
    
    Args:
        df: DataFrame with fund data
        selected_funds: List of selected fund names
        fund_dict: Dictionary mapping fund names to fund IDs
        
    Returns:
        Comparison DataFrame
    """
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
        fund_rows = df[df['FUND_ID'] == fund_id]
        fund_row = fund_rows.iloc[0] if len(fund_rows) > 0 else None
        
        values = []
        for col, label, fmt in metrics:
            if fund_row is not None and col in df.columns and pd.notna(fund_row[col]):
                values.append(f"{fund_row[col]:{fmt}}")
            else:
                values.append("N/A")
        
        # Truncate fund name for column header
        short_name = fund_name[:25] + "..." if len(fund_name) > 25 else fund_name
        comparison_data[short_name] = values
    
    return pd.DataFrame(comparison_data)


def create_statistics_table(fund_history: pd.DataFrame) -> pd.DataFrame:
    """
    Create a statistics summary table for a fund's history.
    
    Args:
        fund_history: DataFrame with historical fund data
        
    Returns:
        Statistics DataFrame
    """
    def safe_stat(series, stat_func, fmt='.2f'):
        try:
            if series.notna().any():
                return f"{stat_func(series):{fmt}}"
        except:
            pass
        return "N/A"
    
    stats_data = {
        'Metric': ['Monthly Yield (%)', 'Total Assets (M)', 'Management Fee (%)', 'Stock Exposure (%)'],
        'Min': [
            safe_stat(fund_history['MONTHLY_YIELD'], lambda s: s.min()),
            safe_stat(fund_history['TOTAL_ASSETS'], lambda s: s.min()),
            safe_stat(fund_history.get('AVG_ANNUAL_MANAGEMENT_FEE', pd.Series()), lambda s: s.min()),
            safe_stat(fund_history.get('STOCK_MARKET_EXPOSURE', pd.Series()), lambda s: s.min()),
        ],
        'Max': [
            safe_stat(fund_history['MONTHLY_YIELD'], lambda s: s.max()),
            safe_stat(fund_history['TOTAL_ASSETS'], lambda s: s.max()),
            safe_stat(fund_history.get('AVG_ANNUAL_MANAGEMENT_FEE', pd.Series()), lambda s: s.max()),
            safe_stat(fund_history.get('STOCK_MARKET_EXPOSURE', pd.Series()), lambda s: s.max()),
        ],
        'Average': [
            safe_stat(fund_history['MONTHLY_YIELD'], lambda s: s.mean()),
            safe_stat(fund_history['TOTAL_ASSETS'], lambda s: s.mean()),
            safe_stat(fund_history.get('AVG_ANNUAL_MANAGEMENT_FEE', pd.Series()), lambda s: s.mean()),
            safe_stat(fund_history.get('STOCK_MARKET_EXPOSURE', pd.Series()), lambda s: s.mean()),
        ],
        'Std Dev': [
            safe_stat(fund_history['MONTHLY_YIELD'], lambda s: s.std()),
            safe_stat(fund_history['TOTAL_ASSETS'], lambda s: s.std()),
            safe_stat(fund_history.get('AVG_ANNUAL_MANAGEMENT_FEE', pd.Series()), lambda s: s.std()),
            safe_stat(fund_history.get('STOCK_MARKET_EXPOSURE', pd.Series()), lambda s: s.std()),
        ],
    }
    
    return pd.DataFrame(stats_data)

