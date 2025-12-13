"""
Application settings and configuration.
Supports environment variables for production deployment.
"""

import os
from pathlib import Path
from typing import Optional
import json

# Base paths
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"

# App metadata
VERSION = "2.2.1"
APP_NAME = "Find Better"
APP_ICON = "📊"

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://data.gov.il/api/3/action/datastore_search")
API_BATCH_SIZE = int(os.getenv("API_BATCH_SIZE", "32000"))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# Cache settings
CACHE_DIR = Path(os.getenv("CACHE_DIR", str(BASE_DIR)))
CACHE_MAX_AGE_HOURS = int(os.getenv("CACHE_MAX_AGE_HOURS", "24"))

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app_data.db'}")
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

# GitHub update settings
GITHUB_REPO = os.getenv("GITHUB_REPO", "moranlevy420/birmanet")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"

# Files to update from GitHub
UPDATE_FILES = [
    "app.py",
    "requirements.txt",
    "run_app.bat",
    "INSTALL_WINDOWS.bat",
    "UNINSTALL_WINDOWS.bat",
    "UPDATE_WINDOWS.bat",
    "config/settings.py",
    "config/datasets.json",
]

# Display columns for the data table
DISPLAY_COLUMNS = [
    'FUND_ID',
    'FUND_NAME',
    'MONTHLY_YIELD',
    'YEAR_TO_DATE_YIELD',
    'AVG_ANNUAL_YIELD_TRAILING_1YR',  # Calculated TTM yield
    'AVG_ANNUAL_YIELD_TRAILING_3YRS',
    'AVG_ANNUAL_YIELD_TRAILING_5YRS',
    'SHARPE_RATIO',
    'STANDARD_DEVIATION',
    'TOTAL_ASSETS',
    'STOCK_MARKET_EXPOSURE',
    'FOREIGN_EXPOSURE',
    'FOREIGN_CURRENCY_EXPOSURE',
    'LIQUID_ASSETS_PERCENT',
    'AVG_ANNUAL_MANAGEMENT_FEE',
    'AVG_DEPOSIT_FEE',
    'FUND_CLASSIFICATION',
]

# Column display labels
COLUMN_LABELS = {
    'FUND_ID': 'Fund ID',
    'FUND_NAME': 'Fund Name',
    'FUND_CLASSIFICATION': 'Classification',
    'TOTAL_ASSETS': 'Total Assets (M)',
    'AVG_ANNUAL_MANAGEMENT_FEE': 'Mgmt Fee (%)',
    'AVG_DEPOSIT_FEE': 'Deposit Fee (%)',
    'MONTHLY_YIELD': 'Monthly Yield (%)',
    'YEAR_TO_DATE_YIELD': 'YTD Yield (%)',
    'AVG_ANNUAL_YIELD_TRAILING_1YR': '1Y Avg Yield (%)',
    'AVG_ANNUAL_YIELD_TRAILING_3YRS': '3Y Avg Yield (%)',
    'AVG_ANNUAL_YIELD_TRAILING_5YRS': '5Y Avg Yield (%)',
    'STANDARD_DEVIATION': 'Std Dev',
    'SHARPE_RATIO': 'Sharpe Ratio',
    'LIQUID_ASSETS_PERCENT': 'Liquid Assets (%)',
    'STOCK_MARKET_EXPOSURE': 'Stock Exposure (%)',
    'FOREIGN_EXPOSURE': 'Foreign Exposure (%)',
    'FOREIGN_CURRENCY_EXPOSURE': 'Currency Exposure (%)',
}

# Chart colors
COLORS = [
    '#2563eb',  # Blue
    '#7c3aed',  # Purple
    '#db2777',  # Pink
    '#ea580c',  # Orange
    '#16a34a',  # Green
    '#0891b2',  # Cyan
    '#4f46e5',  # Indigo
    '#dc2626',  # Red
]


def load_datasets_config() -> dict:
    """Load datasets configuration from JSON file."""
    datasets_path = CONFIG_DIR / "datasets.json"
    if datasets_path.exists():
        with open(datasets_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_cache_path(dataset_type: str) -> Path:
    """Get cache file path for a dataset."""
    return CACHE_DIR / f"{dataset_type}_cache.db"

