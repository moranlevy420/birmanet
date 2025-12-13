"""
Tests for services/cache_service.py
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import time

from services.cache_service import SQLiteCacheService


class TestSQLiteCacheService:
    """Tests for SQLiteCacheService."""
    
    def test_set_and_get(self, cache_service):
        """Test basic set and get operations."""
        data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
            'value': [1.1, 2.2, 3.3]
        })
        
        cache_service.set('test_key', data)
        retrieved = cache_service.get('test_key')
        
        assert retrieved is not None
        assert len(retrieved) == 3
        assert list(retrieved['id']) == [1, 2, 3]
    
    def test_get_nonexistent_key(self, cache_service):
        """Test getting a key that doesn't exist."""
        result = cache_service.get('nonexistent_key')
        
        assert result is None
    
    def test_overwrite_cache(self, cache_service):
        """Test overwriting existing cache."""
        data1 = pd.DataFrame({'id': [1, 2]})
        data2 = pd.DataFrame({'id': [3, 4, 5]})
        
        cache_service.set('overwrite_key', data1)
        cache_service.set('overwrite_key', data2)
        
        result = cache_service.get('overwrite_key')
        
        assert len(result) == 3
        assert list(result['id']) == [3, 4, 5]
    
    def test_date_column_conversion(self, cache_service):
        """Test that REPORT_DATE column is converted back to datetime."""
        data = pd.DataFrame({
            'id': [1, 2],
            'REPORT_DATE': pd.to_datetime(['2023-01-01', '2023-02-01'])
        })
        
        cache_service.set('date_key', data)
        result = cache_service.get('date_key')
        
        assert pd.api.types.is_datetime64_any_dtype(result['REPORT_DATE'])
    
    def test_get_age_hours(self, cache_service):
        """Test getting cache age in hours."""
        data = pd.DataFrame({'id': [1]})
        cache_service.set('age_key', data)
        
        age = cache_service.get_age_hours('age_key')
        
        assert age is not None
        assert age < 1.0  # Should be very recent
    
    def test_get_age_hours_nonexistent(self, cache_service):
        """Test getting age of nonexistent cache."""
        age = cache_service.get_age_hours('nonexistent')
        
        assert age is None
    
    def test_is_valid_fresh_cache(self, cache_service):
        """Test cache validity check for fresh cache."""
        data = pd.DataFrame({'id': [1]})
        cache_service.set('fresh_key', data)
        
        assert cache_service.is_valid('fresh_key') is True
        assert cache_service.is_valid('fresh_key', max_age_hours=24) is True
    
    def test_is_valid_nonexistent(self, cache_service):
        """Test cache validity for nonexistent key."""
        assert cache_service.is_valid('nonexistent') is False
    
    def test_clear_cache(self, cache_service):
        """Test clearing cache."""
        data = pd.DataFrame({'id': [1]})
        cache_service.set('clear_key', data)
        
        # Verify it exists
        assert cache_service.get('clear_key') is not None
        
        # Clear it
        cache_service.clear('clear_key')
        
        # Verify it's gone
        assert cache_service.get('clear_key') is None
    
    def test_clear_nonexistent(self, cache_service):
        """Test clearing nonexistent cache (should not error)."""
        cache_service.clear('nonexistent')  # Should not raise
    
    def test_multiple_keys(self, cache_service):
        """Test managing multiple cache keys."""
        cache_service.set('key1', pd.DataFrame({'id': [1]}))
        cache_service.set('key2', pd.DataFrame({'id': [2]}))
        cache_service.set('key3', pd.DataFrame({'id': [3]}))
        
        assert cache_service.get('key1')['id'].iloc[0] == 1
        assert cache_service.get('key2')['id'].iloc[0] == 2
        assert cache_service.get('key3')['id'].iloc[0] == 3
    
    def test_large_dataframe(self, cache_service):
        """Test caching a large DataFrame."""
        data = pd.DataFrame({
            'id': range(10000),
            'value': [float(i) for i in range(10000)],
            'name': [f'item_{i}' for i in range(10000)]
        })
        
        cache_service.set('large_key', data)
        result = cache_service.get('large_key')
        
        assert len(result) == 10000
    
    def test_empty_dataframe(self, cache_service):
        """Test caching an empty DataFrame."""
        data = pd.DataFrame({'id': [], 'name': []})
        
        cache_service.set('empty_key', data)
        result = cache_service.get('empty_key')
        
        assert result is not None
        assert len(result) == 0
    
    def test_special_characters_in_data(self, cache_service):
        """Test caching data with Hebrew and special characters."""
        data = pd.DataFrame({
            'id': [1, 2],
            'name': ['קרן פנסיה', 'Test "quotes" & <special>']
        })
        
        cache_service.set('hebrew_key', data)
        result = cache_service.get('hebrew_key')
        
        assert result['name'].iloc[0] == 'קרן פנסיה'
        assert 'quotes' in result['name'].iloc[1]

