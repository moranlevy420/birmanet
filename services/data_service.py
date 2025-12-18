"""
Data service for fetching and processing fund data.
"""

import pandas as pd
import requests
from typing import Optional, List
import logging

from models.dataset import Dataset
from services.cache_service import BaseCacheService

logger = logging.getLogger(__name__)


class DataService:
    """Service for fetching and processing fund data from data.gov.il API."""
    
    def __init__(
        self, 
        cache_service: BaseCacheService,
        api_base_url: str,
        batch_size: int = 32000,
        timeout: int = 30
    ):
        self.cache = cache_service
        self.api_base_url = api_base_url
        self.batch_size = batch_size
        self.timeout = timeout
    
    def get_data(self, dataset: Dataset, force_refresh: bool = False) -> pd.DataFrame:
        """
        Get data for a dataset, using cache if available.
        
        Args:
            dataset: Dataset configuration
            force_refresh: If True, bypass cache and fetch from API
            
        Returns:
            DataFrame with fund data
        """
        cache_key = dataset.key
        
        # Check cache first (unless force refresh)
        if not force_refresh and self.cache.is_valid(cache_key):
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"Loaded {len(cached_data)} records from cache for {dataset.name}")
                return cached_data
        
        # Fetch from API
        df = self._fetch_from_api(dataset)
        
        # Save to cache
        if not df.empty:
            self.cache.set(cache_key, df)
        
        return df
    
    def _fetch_from_api(self, dataset: Dataset) -> pd.DataFrame:
        """Fetch data from the API for all resource IDs in a dataset."""
        all_records = []
        
        for resource_id in dataset.resource_ids:
            records = self._fetch_resource(resource_id)
            all_records.extend(records)
        
        if not all_records:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_records)
        df = self._process_data(df, dataset)
        
        return df
    
    def _fetch_resource(self, resource_id: str) -> List[dict]:
        """Fetch all records from a single resource."""
        records = []
        offset = 0
        
        while True:
            try:
                params = {
                    "resource_id": resource_id,
                    "limit": self.batch_size,
                    "offset": offset
                }
                response = requests.get(
                    self.api_base_url, 
                    params=params, 
                    timeout=self.timeout
                )
                data = response.json()
                
                if not data.get("success"):
                    logger.error(f"API Error for resource {resource_id}: {data.get('error')}")
                    break
                
                batch = data["result"]["records"]
                records.extend(batch)
                total = data["result"]["total"]
                
                logger.info(f"Fetched {len(batch)} records (total: {len(records)}/{total})")
                
                if offset + self.batch_size >= total:
                    break
                offset += self.batch_size
                
            except Exception as e:
                logger.error(f"Error fetching resource {resource_id}: {e}")
                break
        
        return records
    
    def _process_data(self, df: pd.DataFrame, dataset: Dataset) -> pd.DataFrame:
        """Process raw data: apply filters, fix encoding, convert values."""
        
        # Apply dataset filter if defined
        if dataset.filter:
            for col, values in dataset.filter.items():
                if col in df.columns:
                    df = df[df[col].isin(values)]
        
        # Fix encoding issues in FUND_NAME (e.g., S1;P500 -> S&P500)
        if 'FUND_NAME' in df.columns:
            df['FUND_NAME'] = df['FUND_NAME'].str.replace('1;', '&', regex=False)
            df['FUND_NAME'] = df['FUND_NAME'].str.replace('&amp;', '&', regex=False)
        
        # Remove IRA funds (בניהול אישי - self-managed)
        if 'FUND_NAME' in df.columns and not df.empty:
            df = df[~df['FUND_NAME'].str.contains('בניהול אישי', na=False)]
        
        # Remove duplicates
        if 'FUND_ID' in df.columns and 'REPORT_PERIOD' in df.columns:
            df = df.drop_duplicates(subset=['FUND_ID', 'REPORT_PERIOD'], keep='first')
        
        # Create date column for plotting
        if 'REPORT_PERIOD' in df.columns:
            df['REPORT_DATE'] = pd.to_datetime(df['REPORT_PERIOD'].astype(str), format='%Y%m')
        
        # Convert exposure values to percentages if needed
        df = self._convert_exposure_to_percentage(df)
        
        # Compute trailing yields (3M, 6M, 1Y) for each fund/month
        df = self._compute_trailing_yields(df)
        
        return df
    
    def _compute_trailing_yields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute trailing compounded yields for 3M, 6M, and 1Y periods."""
        if 'FUND_ID' not in df.columns or 'MONTHLY_YIELD' not in df.columns or 'REPORT_DATE' not in df.columns:
            return df
        
        df = df.sort_values(['FUND_ID', 'REPORT_DATE']).copy()
        
        # Initialize columns
        df['TRAILING_3M_YIELD'] = None
        df['TRAILING_6M_YIELD'] = None
        df['TRAILING_1Y_YIELD'] = None
        
        # Group by fund and compute trailing yields
        for fund_id, fund_df in df.groupby('FUND_ID'):
            fund_df = fund_df.sort_values('REPORT_DATE')
            monthly_yields = fund_df['MONTHLY_YIELD'].values
            indices = fund_df.index.tolist()
            
            for i, idx in enumerate(indices):
                # 3M trailing (need at least 3 months)
                if i >= 2:
                    yields_3m = monthly_yields[i-2:i+1]
                    if len(yields_3m) == 3 and not pd.isna(yields_3m).any():
                        compounded = self._compound_yields(yields_3m)
                        df.loc[idx, 'TRAILING_3M_YIELD'] = compounded
                
                # 6M trailing (need at least 6 months)
                if i >= 5:
                    yields_6m = monthly_yields[i-5:i+1]
                    if len(yields_6m) == 6 and not pd.isna(yields_6m).any():
                        compounded = self._compound_yields(yields_6m)
                        df.loc[idx, 'TRAILING_6M_YIELD'] = compounded
                
                # 1Y trailing (need at least 12 months)
                if i >= 11:
                    yields_1y = monthly_yields[i-11:i+1]
                    if len(yields_1y) == 12 and not pd.isna(yields_1y).any():
                        compounded = self._compound_yields(yields_1y)
                        df.loc[idx, 'TRAILING_1Y_YIELD'] = compounded
        
        logger.info(f"Computed trailing yields: 3M={df['TRAILING_3M_YIELD'].notna().sum()}, "
                   f"6M={df['TRAILING_6M_YIELD'].notna().sum()}, 1Y={df['TRAILING_1Y_YIELD'].notna().sum()}")
        
        return df
    
    def _compound_yields(self, yields: list) -> float:
        """Calculate compounded yield from a list of monthly yields."""
        # (1 + r1/100) * (1 + r2/100) * ... - 1, then * 100
        product = 1.0
        for y in yields:
            product *= (1 + y / 100)
        return round((product - 1) * 100, 2)
    
    def _convert_exposure_to_percentage(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert exposure columns from absolute values to percentages."""
        exposure_cols = ['STOCK_MARKET_EXPOSURE', 'FOREIGN_EXPOSURE', 'FOREIGN_CURRENCY_EXPOSURE']
        
        for col in exposure_cols:
            if col in df.columns and 'TOTAL_ASSETS' in df.columns:
                # If max > 100, values are absolute and need conversion
                if df[col].max() > 100:
                    df[col] = (df[col] / df['TOTAL_ASSETS'] * 100).round(2)
        
        return df
    
    def get_cache_age(self, dataset: Dataset) -> Optional[float]:
        """Get the age of cached data in hours."""
        return self.cache.get_age_hours(dataset.key)
    
    def clear_cache(self, dataset: Dataset) -> None:
        """Clear the cache for a dataset."""
        self.cache.clear(dataset.key)

