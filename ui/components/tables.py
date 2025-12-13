"""
Table components using AgGrid.
"""

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from typing import List, Optional, Tuple

from config.settings import DISPLAY_COLUMNS, COLUMN_LABELS


def create_fund_table(
    df: pd.DataFrame,
    height: int = 280,
    key: str = "fund_table"
) -> Tuple[pd.DataFrame, dict]:
    """
    Create an interactive fund data table using AgGrid.
    
    Args:
        df: DataFrame with fund data
        height: Table height in pixels
        key: Unique key for the table component
        
    Returns:
        Tuple of (sorted_dataframe, grid_response)
    """
    # Prepare display dataframe
    available_cols = [c for c in DISPLAY_COLUMNS if c in df.columns]
    display_df = df[available_cols].copy()
    display_df = display_df.rename(columns=COLUMN_LABELS)
    
    # Pre-sort by YTD Yield
    if 'YTD Yield (%)' in display_df.columns:
        display_df = display_df.sort_values(
            by='YTD Yield (%)', 
            ascending=False, 
            na_position='last'
        )
    display_df = display_df.reset_index(drop=True)
    
    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(display_df)
    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        wrapHeaderText=True,
        autoHeaderHeight=True,
        width=90,
        sortingOrder=['desc', 'asc', None]  # First click = descending
    )
    
    # Configure specific columns
    gb.configure_column("Fund ID", width=70, pinned="left")
    gb.configure_column(
        "Fund Name", 
        width=180, 
        wrapHeaderText=False, 
        pinned="left",
        cellStyle={'direction': 'rtl', 'textAlign': 'right'}
    )
    gb.configure_column(
        "Classification", 
        width=100,
        cellStyle={'direction': 'rtl', 'textAlign': 'right'}
    )
    
    # Default sort by YTD Yield
    if 'YTD Yield (%)' in display_df.columns:
        gb.configure_column('YTD Yield (%)', sort='desc')
    
    # Enable column moving and text selection
    gb.configure_grid_options(
        suppressDragLeaveHidesColumns=True,
        enableCellTextSelection=True,
        ensureDomOrder=True
    )
    
    grid_options = gb.build()
    
    # Create unique key based on data
    data_hash = hash(tuple(display_df['Fund ID'].tolist())) if len(display_df) > 0 else 0
    
    # Display AgGrid table
    grid_response = AgGrid(
        display_df,
        gridOptions=grid_options,
        height=height,
        update_mode=GridUpdateMode.SORTING_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        theme="streamlit",
        allow_unsafe_jscode=True,
        key=f"{key}_{len(display_df)}_{data_hash}"
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

