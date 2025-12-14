"""
Find Better service - Logic for finding better funds.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from models.database import SystemSettings, DEFAULT_THRESHOLDS
from utils.formatters import calculate_compounded_yield


class FindBetterService:
    """Service for finding better funds based on user criteria."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self._init_default_settings()
    
    def _init_default_settings(self):
        """Initialize or update default threshold settings."""
        for key, config in DEFAULT_THRESHOLDS.items():
            existing = self.db.query(SystemSettings).filter(
                SystemSettings.key == key
            ).first()
            
            if not existing:
                # Create new setting
                setting = SystemSettings(
                    key=key,
                    value=config['default'],
                    min_value=config['min'],
                    max_value=config['max'],
                    default_value=config['default'],
                    description=config['description']
                )
                self.db.add(setting)
            else:
                # Update min/max/default if they changed
                existing.min_value = config['min']
                existing.max_value = config['max']
                existing.default_value = config['default']
                existing.description = config['description']
                # Reset value to new default if it was using old default
                if existing.value is None or existing.value == existing.default_value:
                    existing.value = config['default']
        
        self.db.commit()
    
    def get_threshold(self, key: str) -> float:
        """Get a threshold value by key."""
        setting = self.db.query(SystemSettings).filter(
            SystemSettings.key == key
        ).first()
        
        if setting:
            return setting.value if setting.value is not None else setting.default_value
        
        # Fallback to default
        if key in DEFAULT_THRESHOLDS:
            return DEFAULT_THRESHOLDS[key]['default']
        return 0.0
    
    def get_all_thresholds(self) -> Dict[str, dict]:
        """Get all threshold settings."""
        settings = self.db.query(SystemSettings).all()
        result = {}
        
        for s in settings:
            result[s.key] = {
                'value': s.value if s.value is not None else s.default_value,
                'min': s.min_value,
                'max': s.max_value,
                'default': s.default_value,
                'description': s.description
            }
        
        return result
    
    def update_threshold(self, key: str, value: float, updated_by: int = None) -> bool:
        """Update a threshold value."""
        setting = self.db.query(SystemSettings).filter(
            SystemSettings.key == key
        ).first()
        
        if not setting:
            return False
        
        # Validate within range
        if setting.min_value is not None and value < setting.min_value:
            return False
        if setting.max_value is not None and value > setting.max_value:
            return False
        
        setting.value = value
        setting.updated_by = updated_by
        self.db.commit()
        return True
    
    def calculate_period_yield(
        self, 
        all_df: pd.DataFrame, 
        fund_id: int, 
        period_months: int,
        selected_period: int
    ) -> Optional[float]:
        """
        Calculate COMPOUNDED annualized yield for a specific period.
        
        Args:
            all_df: All historical data
            fund_id: Fund to calculate for
            period_months: Number of months (3, 6, 12, 36, 60)
            selected_period: The reference period (YYYYMM)
            
        Returns:
            Compounded annualized yield for the period, or None if insufficient data
        """
        # Filter to this fund
        fund_df = all_df[all_df['FUND_ID'] == fund_id].copy()
        
        if fund_df.empty:
            return None
        
        # Convert period to date
        selected_date = pd.to_datetime(str(selected_period), format='%Y%m')
        start_date = selected_date - pd.DateOffset(months=period_months - 1)
        
        # Filter to date range
        fund_df = fund_df[
            (fund_df['REPORT_DATE'] >= start_date) & 
            (fund_df['REPORT_DATE'] <= selected_date)
        ]
        
        # Need at least 80% of months
        min_months = int(period_months * 0.8)
        if len(fund_df) < min_months:
            return None
        
        if 'MONTHLY_YIELD' not in fund_df.columns:
            return None
        
        # Calculate compounded yield
        return calculate_compounded_yield(fund_df['MONTHLY_YIELD'])
    
    def get_eligible_funds(
        self,
        all_df: pd.DataFrame,
        user_fund: pd.Series,
        period_months: int,
        selected_period: int
    ) -> pd.DataFrame:
        """
        Get eligible funds for comparison.
        
        Criteria:
        1. Same product (FUND_CLASSIFICATION)
        2. Has data for the required yield period
        3. Not the same fund
        """
        # Filter to same classification
        classification = user_fund.get('FUND_CLASSIFICATION')
        if classification:
            eligible = all_df[all_df['FUND_CLASSIFICATION'] == classification].copy()
        else:
            eligible = all_df.copy()
        
        # Exclude user's fund
        user_fund_id = user_fund.get('FUND_ID')
        eligible = eligible[eligible['FUND_ID'] != user_fund_id]
        
        # Get unique funds
        unique_fund_ids = eligible['FUND_ID'].unique()
        
        # For each fund, check if we have enough data and calculate yield
        eligible_funds = []
        
        for fund_id in unique_fund_ids:
            avg_yield = self.calculate_period_yield(
                all_df, fund_id, period_months, selected_period
            )
            
            if avg_yield is not None:
                # Get latest data for this fund
                fund_latest = eligible[
                    (eligible['FUND_ID'] == fund_id) & 
                    (eligible['REPORT_PERIOD'] == selected_period)
                ]
                
                if not fund_latest.empty:
                    fund_data = fund_latest.iloc[0].to_dict()
                    fund_data['CALC_YIELD'] = avg_yield
                    eligible_funds.append(fund_data)
        
        return pd.DataFrame(eligible_funds)
    
    def find_unrestricted_better(
        self,
        eligible_df: pd.DataFrame,
        user_fund: pd.Series,
        user_yield: float,
        top_n: int = 5
    ) -> pd.DataFrame:
        """
        Find better funds with unrestricted strategy.
        
        Criteria:
        1. Yield >= User's yield + yield_threshold
        2. STD <= User's STD + std_threshold (allow slightly higher risk)
        """
        yield_threshold = self.get_threshold('yield_threshold')
        std_threshold = self.get_threshold('std_threshold')
        
        user_std = user_fund.get('STANDARD_DEVIATION', 999)
        
        # Filter by yield improvement
        better = eligible_df[
            eligible_df['CALC_YIELD'] >= (user_yield + yield_threshold)
        ].copy()
        
        # Filter by STD (allow up to std_threshold higher)
        if 'STANDARD_DEVIATION' in better.columns:
            better = better[better['STANDARD_DEVIATION'] <= (user_std + std_threshold)]
        
        # Sort by yield (highest first), then by lowest std
        better = better.sort_values(['CALC_YIELD', 'STANDARD_DEVIATION'], ascending=[False, True])
        
        return better.head(top_n)
    
    def find_similar_strategy_better(
        self,
        eligible_df: pd.DataFrame,
        user_fund: pd.Series,
        user_yield: float,
        top_n: int = 5
    ) -> pd.DataFrame:
        """
        Find better funds with similar strategy.
        
        Criteria:
        1. All exposures within threshold of user's fund
        2. Yield >= User's yield + yield_threshold
        3. STD <= User's STD + std_threshold (allow slightly higher risk)
        """
        yield_threshold = self.get_threshold('yield_threshold')
        std_threshold = self.get_threshold('std_threshold')
        stock_threshold = self.get_threshold('stock_exposure_threshold')
        foreign_threshold = self.get_threshold('foreign_exposure_threshold')
        currency_threshold = self.get_threshold('currency_exposure_threshold')
        liquidity_threshold = self.get_threshold('liquidity_threshold')
        
        user_std = user_fund.get('STANDARD_DEVIATION', 999)
        user_stock = user_fund.get('STOCK_MARKET_EXPOSURE', 0)
        user_foreign = user_fund.get('FOREIGN_EXPOSURE', 0)
        user_currency = user_fund.get('FOREIGN_CURRENCY_EXPOSURE', 0)
        user_liquidity = user_fund.get('LIQUID_ASSETS_PERCENT', 0)
        
        better = eligible_df.copy()
        
        # Filter by yield improvement
        better = better[better['CALC_YIELD'] >= (user_yield + yield_threshold)]
        
        # Filter by STD (allow up to std_threshold higher)
        if 'STANDARD_DEVIATION' in better.columns:
            better = better[better['STANDARD_DEVIATION'] <= (user_std + std_threshold)]
        
        # Filter by exposures (within threshold)
        if 'STOCK_MARKET_EXPOSURE' in better.columns:
            better = better[
                (better['STOCK_MARKET_EXPOSURE'] >= user_stock - stock_threshold) &
                (better['STOCK_MARKET_EXPOSURE'] <= user_stock + stock_threshold)
            ]
        
        if 'FOREIGN_EXPOSURE' in better.columns:
            better = better[
                (better['FOREIGN_EXPOSURE'] >= user_foreign - foreign_threshold) &
                (better['FOREIGN_EXPOSURE'] <= user_foreign + foreign_threshold)
            ]
        
        if 'FOREIGN_CURRENCY_EXPOSURE' in better.columns:
            better = better[
                (better['FOREIGN_CURRENCY_EXPOSURE'] >= user_currency - currency_threshold) &
                (better['FOREIGN_CURRENCY_EXPOSURE'] <= user_currency + currency_threshold)
            ]
        
        if 'LIQUID_ASSETS_PERCENT' in better.columns:
            better = better[
                (better['LIQUID_ASSETS_PERCENT'] >= user_liquidity - liquidity_threshold) &
                (better['LIQUID_ASSETS_PERCENT'] <= user_liquidity + liquidity_threshold)
            ]
        
        # Sort by yield (highest first)
        better = better.sort_values('CALC_YIELD', ascending=False)
        
        return better.head(top_n)

