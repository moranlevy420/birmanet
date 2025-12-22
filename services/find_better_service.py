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
        2. STD <= User's STD - std_threshold (require lower risk)
        """
        yield_threshold = self.get_threshold('yield_threshold')
        std_threshold = self.get_threshold('std_threshold')
        
        user_std = user_fund.get('STANDARD_DEVIATION', 999)
        
        # Filter by yield improvement
        better = eligible_df[
            eligible_df['CALC_YIELD'] >= (user_yield + yield_threshold)
        ].copy()
        
        # Filter by STD (must be lower than user's STD minus threshold)
        if 'STANDARD_DEVIATION' in better.columns:
            better = better[better['STANDARD_DEVIATION'] <= (user_std - std_threshold)]
        
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
        3. STD <= User's STD - std_threshold (require lower risk)
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
        
        # Filter by STD (must be lower than user's STD minus threshold)
        if 'STANDARD_DEVIATION' in better.columns:
            better = better[better['STANDARD_DEVIATION'] <= (user_std - std_threshold)]
        
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
    
    def find_in_strategy_funds(
        self,
        all_df: pd.DataFrame,
        period_df: pd.DataFrame,
        fund_id: int,
        product: str,
        sub_product: Optional[str],
        report_period: int,
        target_std: float,
        target_yield: float,
        yield_period: str,
        target_exposures: Dict[str, float],
        risk_return_threshold: Optional[float] = None,
        exposures_threshold: Optional[float] = None
    ) -> Dict:
        """
        Find all funds that qualify as "In Strategy" funds.
        
        Args:
            all_df: All historical data
            period_df: Data for the selected period
            fund_id: Reference fund ID
            product: Fund product (e.g., 'pension', 'gemel')
            sub_product: Fund sub-product (e.g., 'קרנות חדשות')
            report_period: Report period (YYYYMM format)
            target_std: Target standard deviation
            target_yield: Target yield percentage
            yield_period: Period to check ('1M', '3M', '6M', 'YTD', '1Y', '3Y', '5Y')
            target_exposures: Dict with keys 'equity', 'foreign', 'currency'
            risk_return_threshold: Threshold for yield/STD (uses system default if None)
            exposures_threshold: Threshold for exposures (uses system default if None)
            
        Returns:
            Dict with:
                - funds: List of qualifying funds
                - report_period: The report period used
                - count: Number of qualifying funds
        """
        # Get thresholds (use provided or system defaults)
        yield_threshold = risk_return_threshold if risk_return_threshold is not None else self.get_threshold('yield_threshold')
        std_threshold = risk_return_threshold if risk_return_threshold is not None else self.get_threshold('std_threshold')
        
        # For exposures, use provided threshold or system defaults
        if exposures_threshold is not None:
            stock_threshold = exposures_threshold
            foreign_threshold = exposures_threshold
            currency_threshold = exposures_threshold
        else:
            stock_threshold = self.get_threshold('stock_exposure_threshold')
            foreign_threshold = self.get_threshold('foreign_exposure_threshold')
            currency_threshold = self.get_threshold('currency_exposure_threshold')
        
        # Start with period data
        candidates = period_df.copy()
        
        # Filter by product (FUND_CLASSIFICATION contains product info)
        if sub_product:
            candidates = candidates[candidates['FUND_CLASSIFICATION'] == sub_product]
        
        # Map yield_period to column or compute
        yield_col_map = {
            '1M': 'MONTHLY_YIELD',
            '3M': 'TRAILING_3M_YIELD',
            '6M': 'TRAILING_6M_YIELD',
            'YTD': 'YEAR_TO_DATE_YIELD',
            '1Y': 'TRAILING_1Y_YIELD',
            '3Y': 'AVG_ANNUAL_YIELD_TRAILING_3YRS',
            '5Y': 'AVG_ANNUAL_YIELD_TRAILING_5YRS',
        }
        
        yield_col = yield_col_map.get(yield_period, 'TRAILING_1Y_YIELD')
        
        # Check if yield column exists in data
        if yield_col not in candidates.columns or candidates[yield_col].isna().all():
            # Need to compute from monthly yields
            period_months_map = {'1M': 1, '3M': 3, '6M': 6, '1Y': 12, '3Y': 36, '5Y': 60}
            period_months = period_months_map.get(yield_period, 12)
            
            # Calculate yield for each fund
            calc_yields = {}
            for fid in candidates['FUND_ID'].unique():
                calc_yield = self.calculate_period_yield(all_df, fid, period_months, report_period)
                if calc_yield is not None:
                    calc_yields[fid] = calc_yield
            
            # Add calculated yield to candidates
            candidates['CALC_YIELD'] = candidates['FUND_ID'].map(calc_yields)
            yield_col = 'CALC_YIELD'
        
        # Filter: funds with valid yield data
        candidates = candidates[candidates[yield_col].notna()].copy()
        
        # Filter by Yield: Fund Yield >= (target_yield + threshold)
        candidates = candidates[candidates[yield_col] >= (target_yield + yield_threshold)]
        
        # Filter by STD: Fund STD <= (target_std - threshold)
        # Only consider funds with non-null STD
        if 'STANDARD_DEVIATION' in candidates.columns:
            candidates = candidates[
                (candidates['STANDARD_DEVIATION'].notna()) &
                (candidates['STANDARD_DEVIATION'] <= (target_std - std_threshold))
            ]
        
        # Filter by Strategy (Exposures)
        # All exposures must be NOT NULL and within target ± threshold
        
        # Equity exposure
        if 'equity' in target_exposures and target_exposures['equity'] is not None:
            target_equity = target_exposures['equity']
            if 'STOCK_MARKET_EXPOSURE' in candidates.columns:
                candidates = candidates[
                    (candidates['STOCK_MARKET_EXPOSURE'].notna()) &
                    (candidates['STOCK_MARKET_EXPOSURE'] >= (target_equity - stock_threshold)) &
                    (candidates['STOCK_MARKET_EXPOSURE'] <= (target_equity + stock_threshold))
                ]
        
        # Foreign exposure
        if 'foreign' in target_exposures and target_exposures['foreign'] is not None:
            target_foreign = target_exposures['foreign']
            if 'FOREIGN_EXPOSURE' in candidates.columns:
                candidates = candidates[
                    (candidates['FOREIGN_EXPOSURE'].notna()) &
                    (candidates['FOREIGN_EXPOSURE'] >= (target_foreign - foreign_threshold)) &
                    (candidates['FOREIGN_EXPOSURE'] <= (target_foreign + foreign_threshold))
                ]
        
        # Currency exposure
        if 'currency' in target_exposures and target_exposures['currency'] is not None:
            target_currency = target_exposures['currency']
            if 'FOREIGN_CURRENCY_EXPOSURE' in candidates.columns:
                candidates = candidates[
                    (candidates['FOREIGN_CURRENCY_EXPOSURE'].notna()) &
                    (candidates['FOREIGN_CURRENCY_EXPOSURE'] >= (target_currency - currency_threshold)) &
                    (candidates['FOREIGN_CURRENCY_EXPOSURE'] <= (target_currency + currency_threshold))
                ]
        
        # Prepare return data
        result_funds = []
        for _, row in candidates.iterrows():
            fund_data = {
                'fund_id': row.get('FUND_ID'),
                'fund_name': row.get('FUND_NAME'),
                'classification': row.get('FUND_CLASSIFICATION'),
                # Risk/Return data
                'yield_value': row.get(yield_col),
                'yield_period': yield_period,
                'monthly_yield': row.get('MONTHLY_YIELD'),
                'ytd_yield': row.get('YEAR_TO_DATE_YIELD'),
                'trailing_1y': row.get('TRAILING_1Y_YIELD') or row.get('AVG_ANNUAL_YIELD_TRAILING_1YR'),
                'trailing_3y': row.get('AVG_ANNUAL_YIELD_TRAILING_3YRS'),
                'trailing_5y': row.get('AVG_ANNUAL_YIELD_TRAILING_5YRS'),
                'std_dev': row.get('STANDARD_DEVIATION'),
                'sharpe': row.get('SHARPE_RATIO'),
                # Exposures data
                'stock_exposure': row.get('STOCK_MARKET_EXPOSURE'),
                'foreign_exposure': row.get('FOREIGN_EXPOSURE'),
                'currency_exposure': row.get('FOREIGN_CURRENCY_EXPOSURE'),
                'liquid_assets': row.get('LIQUID_ASSETS_PERCENT'),
            }
            result_funds.append(fund_data)
        
        return {
            'funds': result_funds,
            'report_period': report_period,
            'count': len(result_funds),
            'yield_period': yield_period,
            'target_yield': target_yield,
            'target_std': target_std,
            'target_exposures': target_exposures,
            'thresholds': {
                'yield': yield_threshold,
                'std': std_threshold,
                'stock': stock_threshold,
                'foreign': foreign_threshold,
                'currency': currency_threshold,
            }
        }

