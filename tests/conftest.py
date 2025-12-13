"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, User, SystemSettings, DEFAULT_THRESHOLDS
from models.dataset import Dataset, SubFilter, PopulationFilter, DatasetRegistry
from services.auth_service import AuthService
from services.cache_service import SQLiteCacheService
from services.find_better_service import FindBetterService


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def db_session(temp_dir):
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def auth_service(db_session):
    """Create an AuthService instance for testing."""
    return AuthService(db_session)


@pytest.fixture
def find_better_service(db_session):
    """Create a FindBetterService instance for testing."""
    return FindBetterService(db_session)


@pytest.fixture
def cache_service(temp_dir):
    """Create a SQLiteCacheService instance for testing."""
    return SQLiteCacheService(cache_dir=temp_dir, max_age_hours=24)


@pytest.fixture
def sample_user(auth_service):
    """Create a sample user for testing."""
    user, temp_password = auth_service.create_user(
        email="test@example.com",
        name="Test User",
        role="member",
        password="TestPass123"
    )
    return user, "TestPass123"


@pytest.fixture
def admin_user(auth_service):
    """Create an admin user for testing."""
    user, temp_password = auth_service.create_user(
        email="admin@example.com",
        name="Admin User",
        role="admin",
        password="AdminPass123"
    )
    return user, "AdminPass123"


@pytest.fixture
def sample_fund_data():
    """Create sample fund data for testing."""
    dates = pd.date_range(start='2023-01-01', periods=24, freq='ME')
    periods = [int(d.strftime('%Y%m')) for d in dates]
    
    data = []
    for i, (date, period) in enumerate(zip(dates, periods)):
        # Fund 1 - Good performer
        data.append({
            'FUND_ID': 1001,
            'FUND_NAME': 'Test Fund Alpha',
            'FUND_CLASSIFICATION': 'General',
            'MANAGING_CORPORATION': 'Test Corp A',
            'REPORT_DATE': date,
            'REPORT_PERIOD': period,
            'MONTHLY_YIELD': 1.5 + (i % 5) * 0.1,
            'YEAR_TO_DATE_YIELD': (i + 1) * 1.2,
            'TOTAL_ASSETS': 1000 + i * 50,
            'STANDARD_DEVIATION': 3.5,
            'STOCK_MARKET_EXPOSURE': 45.0,
            'FOREIGN_EXPOSURE': 30.0,
            'FOREIGN_CURRENCY_EXPOSURE': 20.0,
            'LIQUID_ASSETS_PERCENT': 15.0,
            'AVG_ANNUAL_MANAGEMENT_FEE': 0.5,
            'SHARPE_RATIO': 1.2
        })
        
        # Fund 2 - Moderate performer
        data.append({
            'FUND_ID': 1002,
            'FUND_NAME': 'Test Fund Beta',
            'FUND_CLASSIFICATION': 'General',
            'MANAGING_CORPORATION': 'Test Corp B',
            'REPORT_DATE': date,
            'REPORT_PERIOD': period,
            'MONTHLY_YIELD': 1.0 + (i % 4) * 0.1,
            'YEAR_TO_DATE_YIELD': (i + 1) * 0.9,
            'TOTAL_ASSETS': 800 + i * 30,
            'STANDARD_DEVIATION': 4.0,
            'STOCK_MARKET_EXPOSURE': 50.0,
            'FOREIGN_EXPOSURE': 35.0,
            'FOREIGN_CURRENCY_EXPOSURE': 25.0,
            'LIQUID_ASSETS_PERCENT': 10.0,
            'AVG_ANNUAL_MANAGEMENT_FEE': 0.6,
            'SHARPE_RATIO': 0.9
        })
        
        # Fund 3 - Lower performer, similar strategy to Fund 1
        data.append({
            'FUND_ID': 1003,
            'FUND_NAME': 'Test Fund Gamma',
            'FUND_CLASSIFICATION': 'General',
            'MANAGING_CORPORATION': 'Test Corp A',
            'REPORT_DATE': date,
            'REPORT_PERIOD': period,
            'MONTHLY_YIELD': 0.8 + (i % 3) * 0.1,
            'YEAR_TO_DATE_YIELD': (i + 1) * 0.7,
            'TOTAL_ASSETS': 500 + i * 20,
            'STANDARD_DEVIATION': 3.2,
            'STOCK_MARKET_EXPOSURE': 43.0,
            'FOREIGN_EXPOSURE': 28.0,
            'FOREIGN_CURRENCY_EXPOSURE': 18.0,
            'LIQUID_ASSETS_PERCENT': 17.0,
            'AVG_ANNUAL_MANAGEMENT_FEE': 0.7,
            'SHARPE_RATIO': 0.7
        })
        
        # Fund 4 - Different classification
        data.append({
            'FUND_ID': 1004,
            'FUND_NAME': 'Test Fund Delta',
            'FUND_CLASSIFICATION': 'Conservative',
            'MANAGING_CORPORATION': 'Test Corp C',
            'REPORT_DATE': date,
            'REPORT_PERIOD': period,
            'MONTHLY_YIELD': 0.5 + (i % 2) * 0.1,
            'YEAR_TO_DATE_YIELD': (i + 1) * 0.5,
            'TOTAL_ASSETS': 2000 + i * 100,
            'STANDARD_DEVIATION': 1.5,
            'STOCK_MARKET_EXPOSURE': 20.0,
            'FOREIGN_EXPOSURE': 15.0,
            'FOREIGN_CURRENCY_EXPOSURE': 10.0,
            'LIQUID_ASSETS_PERCENT': 30.0,
            'AVG_ANNUAL_MANAGEMENT_FEE': 0.3,
            'SHARPE_RATIO': 1.0
        })
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_dataset_config(temp_dir):
    """Create a sample datasets.json configuration."""
    config = {
        "test_product": {
            "name": "Test Product",
            "name_heb": "מוצר בדיקה",
            "resource_ids": ["test-resource-1", "test-resource-2"],
            "sub_filters": {
                "column": "FUND_CLASSIFICATION",
                "options": ["General", "Conservative"]
            }
        },
        "test_product_2": {
            "name": "Test Product 2",
            "name_heb": "מוצר בדיקה 2",
            "resource_ids": ["test-resource-3"],
            "filter": {
                "FUND_CLASSIFICATION": ["Special"]
            },
            "population_filter": {
                "column": "TARGET_POPULATION",
                "exclude_values": ["Excluded"]
            }
        }
    }
    
    import json
    config_path = temp_dir / "datasets.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f)
    
    return config_path

