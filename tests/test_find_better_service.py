"""
Tests for services/find_better_service.py
"""

import pytest
import pandas as pd

from services.find_better_service import FindBetterService


class TestThresholdManagement:
    """Tests for threshold settings management."""
    
    def test_default_thresholds_initialized(self, find_better_service):
        """Test that default thresholds are initialized."""
        thresholds = find_better_service.get_all_thresholds()
        
        assert 'yield_threshold' in thresholds
        assert 'std_threshold' in thresholds
        assert 'stock_exposure_threshold' in thresholds
        assert 'foreign_exposure_threshold' in thresholds
        assert 'currency_exposure_threshold' in thresholds
        assert 'liquidity_threshold' in thresholds
    
    def test_get_threshold(self, find_better_service):
        """Test getting a specific threshold."""
        yield_threshold = find_better_service.get_threshold('yield_threshold')
        
        assert yield_threshold >= 0
        assert yield_threshold <= 5.0
    
    def test_get_threshold_nonexistent(self, find_better_service):
        """Test getting nonexistent threshold returns fallback."""
        value = find_better_service.get_threshold('nonexistent_key')
        
        assert value == 0.0
    
    def test_update_threshold_success(self, find_better_service):
        """Test updating a threshold."""
        result = find_better_service.update_threshold('yield_threshold', 0.5)
        
        assert result is True
        assert find_better_service.get_threshold('yield_threshold') == 0.5
    
    def test_update_threshold_out_of_range_low(self, find_better_service):
        """Test updating threshold below minimum."""
        result = find_better_service.update_threshold('yield_threshold', -1.0)
        
        assert result is False
    
    def test_update_threshold_out_of_range_high(self, find_better_service):
        """Test updating threshold above maximum."""
        result = find_better_service.update_threshold('yield_threshold', 100.0)
        
        assert result is False
    
    def test_update_nonexistent_threshold(self, find_better_service):
        """Test updating nonexistent threshold."""
        result = find_better_service.update_threshold('fake_threshold', 1.0)
        
        assert result is False


class TestCalculatePeriodYield:
    """Tests for period yield calculation."""
    
    def test_calculate_1y_yield(self, find_better_service, sample_fund_data):
        """Test 1-year yield calculation."""
        result = find_better_service.calculate_period_yield(
            sample_fund_data,
            fund_id=1001,
            period_months=12,
            selected_period=202312
        )
        
        assert result is not None
        assert isinstance(result, float)
    
    def test_calculate_3m_yield(self, find_better_service, sample_fund_data):
        """Test 3-month yield calculation."""
        result = find_better_service.calculate_period_yield(
            sample_fund_data,
            fund_id=1001,
            period_months=3,
            selected_period=202312
        )
        
        assert result is not None
    
    def test_calculate_yield_nonexistent_fund(self, find_better_service, sample_fund_data):
        """Test yield calculation for nonexistent fund."""
        result = find_better_service.calculate_period_yield(
            sample_fund_data,
            fund_id=9999,
            period_months=12,
            selected_period=202312
        )
        
        assert result is None
    
    def test_calculate_yield_insufficient_data(self, find_better_service):
        """Test yield calculation with insufficient data."""
        # Only 2 months of data
        data = pd.DataFrame({
            'FUND_ID': [1, 1],
            'REPORT_DATE': pd.to_datetime(['2023-11-01', '2023-12-01']),
            'REPORT_PERIOD': [202311, 202312],
            'MONTHLY_YIELD': [1.0, 1.5]
        })
        
        result = find_better_service.calculate_period_yield(
            data,
            fund_id=1,
            period_months=12,  # Needs 12 months
            selected_period=202312
        )
        
        assert result is None  # Not enough data
    
    def test_calculate_yield_empty_dataframe(self, find_better_service):
        """Test yield calculation with empty DataFrame (with proper columns)."""
        empty_df = pd.DataFrame(columns=['FUND_ID', 'REPORT_DATE', 'REPORT_PERIOD', 'MONTHLY_YIELD'])
        
        result = find_better_service.calculate_period_yield(
            empty_df,
            fund_id=1,
            period_months=12,
            selected_period=202312
        )
        
        assert result is None


class TestGetEligibleFunds:
    """Tests for getting eligible funds for comparison."""
    
    def test_get_eligible_funds_same_classification(self, find_better_service, sample_fund_data):
        """Test that eligible funds have same classification."""
        user_fund = sample_fund_data[sample_fund_data['FUND_ID'] == 1001].iloc[0]
        
        eligible = find_better_service.get_eligible_funds(
            sample_fund_data,
            user_fund,
            period_months=12,
            selected_period=202312
        )
        
        # Should include funds 1002 and 1003 (same classification)
        # Should NOT include fund 1004 (different classification)
        fund_ids = eligible['FUND_ID'].unique().tolist()
        
        assert 1001 not in fund_ids  # User's fund excluded
        assert 1002 in fund_ids or 1003 in fund_ids  # Same classification
        assert 1004 not in fund_ids  # Different classification
    
    def test_get_eligible_funds_excludes_user_fund(self, find_better_service, sample_fund_data):
        """Test that user's own fund is excluded."""
        user_fund = sample_fund_data[sample_fund_data['FUND_ID'] == 1001].iloc[0]
        
        eligible = find_better_service.get_eligible_funds(
            sample_fund_data,
            user_fund,
            period_months=12,
            selected_period=202312
        )
        
        assert 1001 not in eligible['FUND_ID'].values
    
    def test_get_eligible_funds_has_yield(self, find_better_service, sample_fund_data):
        """Test that eligible funds have calculated yield."""
        user_fund = sample_fund_data[sample_fund_data['FUND_ID'] == 1001].iloc[0]
        
        eligible = find_better_service.get_eligible_funds(
            sample_fund_data,
            user_fund,
            period_months=12,
            selected_period=202312
        )
        
        assert 'CALC_YIELD' in eligible.columns
        assert eligible['CALC_YIELD'].notna().all()


class TestFindUnrestrictedBetter:
    """Tests for finding better funds with unrestricted strategy."""
    
    def test_find_unrestricted_better(self, find_better_service, sample_fund_data):
        """Test finding better funds without exposure restrictions."""
        # Use fund 1003 (lower performer) as user fund
        user_fund = sample_fund_data[
            (sample_fund_data['FUND_ID'] == 1003) & 
            (sample_fund_data['REPORT_PERIOD'] == 202312)
        ].iloc[0]
        user_yield = 0.9  # Low yield
        
        eligible = find_better_service.get_eligible_funds(
            sample_fund_data,
            user_fund,
            period_months=12,
            selected_period=202312
        )
        
        better = find_better_service.find_unrestricted_better(
            eligible,
            user_fund,
            user_yield,
            top_n=5
        )
        
        # Should find funds with better yield
        if len(better) > 0:
            assert all(better['CALC_YIELD'] >= user_yield)
    
    def test_find_unrestricted_better_respects_std(self, find_better_service, sample_fund_data):
        """Test that STD threshold is respected."""
        user_fund = sample_fund_data[
            (sample_fund_data['FUND_ID'] == 1001) & 
            (sample_fund_data['REPORT_PERIOD'] == 202312)
        ].iloc[0]
        user_yield = 1.5
        user_std = user_fund['STANDARD_DEVIATION']
        
        eligible = find_better_service.get_eligible_funds(
            sample_fund_data,
            user_fund,
            period_months=12,
            selected_period=202312
        )
        
        better = find_better_service.find_unrestricted_better(
            eligible,
            user_fund,
            user_yield,
            top_n=10
        )
        
        std_threshold = find_better_service.get_threshold('std_threshold')
        
        if len(better) > 0 and 'STANDARD_DEVIATION' in better.columns:
            assert all(better['STANDARD_DEVIATION'] <= user_std + std_threshold)
    
    def test_find_unrestricted_better_top_n(self, find_better_service, sample_fund_data):
        """Test that top_n limit is respected."""
        user_fund = sample_fund_data[
            (sample_fund_data['FUND_ID'] == 1003) & 
            (sample_fund_data['REPORT_PERIOD'] == 202312)
        ].iloc[0]
        
        eligible = find_better_service.get_eligible_funds(
            sample_fund_data,
            user_fund,
            period_months=12,
            selected_period=202312
        )
        
        better = find_better_service.find_unrestricted_better(
            eligible,
            user_fund,
            user_yield=0.5,
            top_n=2
        )
        
        assert len(better) <= 2


class TestFindSimilarStrategyBetter:
    """Tests for finding better funds with similar strategy."""
    
    def test_find_similar_strategy_better(self, find_better_service, sample_fund_data):
        """Test finding better funds with similar exposures."""
        user_fund = sample_fund_data[
            (sample_fund_data['FUND_ID'] == 1003) & 
            (sample_fund_data['REPORT_PERIOD'] == 202312)
        ].iloc[0]
        user_yield = 0.9
        
        eligible = find_better_service.get_eligible_funds(
            sample_fund_data,
            user_fund,
            period_months=12,
            selected_period=202312
        )
        
        better = find_better_service.find_similar_strategy_better(
            eligible,
            user_fund,
            user_yield,
            top_n=5
        )
        
        # If funds found, they should have similar exposures
        if len(better) > 0:
            stock_threshold = find_better_service.get_threshold('stock_exposure_threshold')
            user_stock = user_fund['STOCK_MARKET_EXPOSURE']
            
            if 'STOCK_MARKET_EXPOSURE' in better.columns:
                for _, fund in better.iterrows():
                    diff = abs(fund['STOCK_MARKET_EXPOSURE'] - user_stock)
                    assert diff <= stock_threshold
    
    def test_find_similar_strategy_respects_all_exposures(self, find_better_service, sample_fund_data):
        """Test that all exposure thresholds are checked."""
        user_fund = sample_fund_data[
            (sample_fund_data['FUND_ID'] == 1001) & 
            (sample_fund_data['REPORT_PERIOD'] == 202312)
        ].iloc[0]
        user_yield = 1.0
        
        eligible = find_better_service.get_eligible_funds(
            sample_fund_data,
            user_fund,
            period_months=12,
            selected_period=202312
        )
        
        better = find_better_service.find_similar_strategy_better(
            eligible,
            user_fund,
            user_yield,
            top_n=10
        )
        
        if len(better) > 0:
            foreign_threshold = find_better_service.get_threshold('foreign_exposure_threshold')
            currency_threshold = find_better_service.get_threshold('currency_exposure_threshold')
            liquidity_threshold = find_better_service.get_threshold('liquidity_threshold')
            
            user_foreign = user_fund['FOREIGN_EXPOSURE']
            user_currency = user_fund['FOREIGN_CURRENCY_EXPOSURE']
            user_liquidity = user_fund['LIQUID_ASSETS_PERCENT']
            
            for _, fund in better.iterrows():
                if 'FOREIGN_EXPOSURE' in fund:
                    assert abs(fund['FOREIGN_EXPOSURE'] - user_foreign) <= foreign_threshold
                if 'FOREIGN_CURRENCY_EXPOSURE' in fund:
                    assert abs(fund['FOREIGN_CURRENCY_EXPOSURE'] - user_currency) <= currency_threshold
                if 'LIQUID_ASSETS_PERCENT' in fund:
                    assert abs(fund['LIQUID_ASSETS_PERCENT'] - user_liquidity) <= liquidity_threshold
    
    def test_find_similar_returns_empty_when_no_match(self, find_better_service, sample_fund_data):
        """Test that empty DataFrame is returned when no funds match criteria."""
        # Use fund 1001 with very high yield requirement (no fund will match)
        user_fund = sample_fund_data[
            (sample_fund_data['FUND_ID'] == 1001) & 
            (sample_fund_data['REPORT_PERIOD'] == 202312)
        ].iloc[0]
        
        # Get eligible funds
        eligible = find_better_service.get_eligible_funds(
            sample_fund_data,
            user_fund,
            period_months=12,
            selected_period=202312
        )
        
        # Use a very high yield requirement that no fund will beat
        better = find_better_service.find_similar_strategy_better(
            eligible,
            user_fund,
            user_yield=100.0,  # No fund can beat 100% yield
            top_n=5
        )
        
        assert len(better) == 0


class TestIntegration:
    """Integration tests for the full Find Better flow."""
    
    def test_full_find_better_flow(self, find_better_service, sample_fund_data):
        """Test the complete flow of finding better funds."""
        # Step 1: Select user's fund
        selected_period = 202312
        user_fund = sample_fund_data[
            (sample_fund_data['FUND_ID'] == 1003) & 
            (sample_fund_data['REPORT_PERIOD'] == selected_period)
        ].iloc[0]
        
        # Step 2: Calculate user's yield
        user_yield = find_better_service.calculate_period_yield(
            sample_fund_data,
            fund_id=1003,
            period_months=12,
            selected_period=selected_period
        )
        
        assert user_yield is not None
        
        # Step 3: Get eligible funds
        eligible = find_better_service.get_eligible_funds(
            sample_fund_data,
            user_fund,
            period_months=12,
            selected_period=selected_period
        )
        
        assert len(eligible) > 0
        
        # Step 4: Find unrestricted better
        unrestricted = find_better_service.find_unrestricted_better(
            eligible,
            user_fund,
            user_yield,
            top_n=5
        )
        
        # Step 5: Find similar strategy better
        similar = find_better_service.find_similar_strategy_better(
            eligible,
            user_fund,
            user_yield,
            top_n=5
        )
        
        # Both should return DataFrames (may be empty)
        assert isinstance(unrestricted, pd.DataFrame)
        assert isinstance(similar, pd.DataFrame)

