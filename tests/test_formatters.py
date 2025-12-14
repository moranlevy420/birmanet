"""
Tests for utils/formatters.py
"""

import pytest
import pandas as pd
from datetime import datetime

from utils.formatters import (
    format_period,
    get_short_unique_name,
    format_number,
    calculate_trailing_1y_yield,
    calculate_compounded_yield
)


class TestFormatPeriod:
    """Tests for format_period function."""
    
    def test_format_january(self):
        """Test formatting January period."""
        assert format_period(202401) == "Jan 2024"
    
    def test_format_december(self):
        """Test formatting December period."""
        assert format_period(202312) == "Dec 2023"
    
    def test_format_june(self):
        """Test formatting June period."""
        assert format_period(202306) == "Jun 2023"
    
    def test_format_invalid_month_zero(self):
        """Test handling invalid month (0)."""
        assert format_period(202400) == "202400"
    
    def test_format_invalid_month_thirteen(self):
        """Test handling invalid month (13)."""
        assert format_period(202413) == "202413"
    
    def test_format_old_year(self):
        """Test formatting old year."""
        assert format_period(201901) == "Jan 2019"


class TestGetShortUniqueName:
    """Tests for get_short_unique_name function."""
    
    def test_unique_first_word(self):
        """Test when first word is unique."""
        names = ["Alpha Fund General", "Beta Fund Conservative", "Gamma Fund"]
        assert get_short_unique_name("Alpha Fund General", names) == "Alpha"
    
    def test_non_unique_first_word(self):
        """Test when first word is not unique."""
        names = ["Test Fund Alpha", "Test Fund Beta", "Other Fund"]
        result = get_short_unique_name("Test Fund Alpha", names)
        assert "Test" in result and "Alpha" in result
    
    def test_non_string_name(self):
        """Test handling non-string names (NaN)."""
        result = get_short_unique_name(float('nan'), ["Some Fund"])
        assert result == "nan"
    
    def test_empty_name(self):
        """Test handling empty name."""
        result = get_short_unique_name("", ["Some Fund"])
        assert result == ""
    
    def test_single_word_name(self):
        """Test single word name."""
        names = ["SingleWord", "Other Fund"]
        assert get_short_unique_name("SingleWord", names) == "SingleWord"
    
    def test_filter_non_string_all_names(self):
        """Test that non-string values in all_names are filtered."""
        names = ["Test Fund", float('nan'), None, "Other Fund"]
        result = get_short_unique_name("Test Fund", names)
        assert result == "Test"


class TestFormatNumber:
    """Tests for format_number function."""
    
    def test_basic_format(self):
        """Test basic number formatting."""
        assert format_number(1234.567) == "1,234.57"
    
    def test_with_prefix(self):
        """Test formatting with prefix."""
        assert format_number(1234.5, prefix="$") == "$1,234.50"
    
    def test_with_suffix(self):
        """Test formatting with suffix."""
        assert format_number(75.5, suffix="%") == "75.50%"
    
    def test_with_prefix_and_suffix(self):
        """Test formatting with both prefix and suffix."""
        assert format_number(1234.5, prefix="$", suffix=" USD") == "$1,234.50 USD"
    
    def test_custom_decimals(self):
        """Test custom decimal places."""
        assert format_number(3.14159, decimals=4) == "3.1416"
    
    def test_none_value(self):
        """Test handling None value."""
        assert format_number(None) == "N/A"
    
    def test_zero_value(self):
        """Test zero value."""
        assert format_number(0) == "0.00"
    
    def test_negative_value(self):
        """Test negative value."""
        assert format_number(-123.45) == "-123.45"


class TestCalculateCompoundedYield:
    """Tests for calculate_compounded_yield function."""
    
    def test_constant_1_percent_monthly(self):
        """Test 1% monthly yield for 12 months = ~12.68% annual."""
        monthly_yields = pd.Series([1.0] * 12)
        result = calculate_compounded_yield(monthly_yields)
        # (1.01)^12 - 1 = 0.1268 = 12.68%
        assert abs(result - 12.68) < 0.01
    
    def test_constant_0_5_percent_monthly(self):
        """Test 0.5% monthly yield for 12 months = ~6.17% annual."""
        monthly_yields = pd.Series([0.5] * 12)
        result = calculate_compounded_yield(monthly_yields)
        # (1.005)^12 - 1 = 0.0617 = 6.17%
        assert abs(result - 6.17) < 0.01
    
    def test_annualization_for_6_months(self):
        """Test annualization for less than 12 months."""
        # 1% monthly for 6 months, annualized
        monthly_yields = pd.Series([1.0] * 6)
        result = calculate_compounded_yield(monthly_yields)
        # (1.01^6)^(12/6) - 1 = 1.01^12 - 1 = 12.68%
        assert abs(result - 12.68) < 0.01
    
    def test_negative_yields(self):
        """Test negative monthly yields."""
        monthly_yields = pd.Series([-1.0] * 12)
        result = calculate_compounded_yield(monthly_yields)
        # (0.99)^12 - 1 = -11.36%
        assert abs(result - (-11.36)) < 0.1
    
    def test_empty_series(self):
        """Test empty series returns None."""
        result = calculate_compounded_yield(pd.Series([]))
        assert result is None
    
    def test_mixed_yields(self):
        """Test mixed positive and negative yields."""
        monthly_yields = pd.Series([2.0, -1.0, 1.5, 0.5, -0.5, 1.0])
        result = calculate_compounded_yield(monthly_yields)
        assert result is not None
        # Should be annualized (multiplied out and raised to 12/6)


class TestCalculateTrailing1YYield:
    """Tests for calculate_trailing_1y_yield function."""
    
    def test_basic_calculation(self, sample_fund_data):
        """Test basic TTM yield calculation."""
        selected_period = 202312
        period_df = sample_fund_data[sample_fund_data['REPORT_PERIOD'] == selected_period]
        
        result = calculate_trailing_1y_yield(period_df, sample_fund_data, selected_period)
        
        assert 'AVG_ANNUAL_YIELD_TRAILING_1YR' in result.columns
        # All funds should have values (they have 24 months of data)
        assert result['AVG_ANNUAL_YIELD_TRAILING_1YR'].notna().sum() > 0
    
    def test_insufficient_data(self):
        """Test with insufficient historical data."""
        # Only 3 months of data
        dates = pd.date_range(start='2023-10-01', periods=3, freq='ME')
        periods = [int(d.strftime('%Y%m')) for d in dates]
        
        data = []
        for date, period in zip(dates, periods):
            data.append({
                'FUND_ID': 1,
                'FUND_NAME': 'Test',
                'REPORT_DATE': date,
                'REPORT_PERIOD': period,
                'MONTHLY_YIELD': 1.0
            })
        
        all_df = pd.DataFrame(data)
        period_df = all_df[all_df['REPORT_PERIOD'] == periods[-1]]
        
        result = calculate_trailing_1y_yield(period_df, all_df, periods[-1])
        
        # Should have NaN because not enough data
        assert result['AVG_ANNUAL_YIELD_TRAILING_1YR'].isna().all()
    
    def test_missing_monthly_yield_column(self):
        """Test handling missing MONTHLY_YIELD column."""
        data = {
            'FUND_ID': [1, 1],
            'FUND_NAME': ['Test', 'Test'],
            'REPORT_DATE': pd.date_range(start='2023-01-01', periods=2, freq='ME'),
            'REPORT_PERIOD': [202301, 202302]
        }
        all_df = pd.DataFrame(data)
        period_df = all_df[all_df['REPORT_PERIOD'] == 202302]
        
        result = calculate_trailing_1y_yield(period_df, all_df, 202302)
        
        assert 'AVG_ANNUAL_YIELD_TRAILING_1YR' in result.columns
        assert result['AVG_ANNUAL_YIELD_TRAILING_1YR'].isna().all()

