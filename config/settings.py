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
VERSION = "2.7.1"
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
    # Streamlit config (fixes theme consistency across platforms)
    ".streamlit/config.toml",
    # Main files
    "app.py",
    "requirements.txt",
    "run_app.bat",
    "INSTALL_WINDOWS.bat",
    "UNINSTALL_WINDOWS.bat",
    "UPDATE_WINDOWS.bat",
    "RESET_PASSWORD.bat",
    "alembic.ini",
    "manage.py",
    # Config
    "config/__init__.py",
    "config/settings.py",
    "config/datasets.json",
    # Models
    "models/__init__.py",
    "models/dataset.py",
    "models/database.py",
    # Services
    "services/__init__.py",
    "services/cache_service.py",
    "services/data_service.py",
    "services/db_service.py",
    "services/update_service.py",
    "services/auth_service.py",
    "services/find_better_service.py",
    # UI
    "ui/__init__.py",
    "ui/styles.py",
    "ui/components/__init__.py",
    "ui/components/charts.py",
    "ui/components/tables.py",
    "ui/components/sidebar.py",
    "ui/components/auth.py",
    "ui/pages/__init__.py",
    "ui/pages/world_view.py",
    "ui/pages/charts_page.py",
    "ui/pages/compare.py",
    "ui/pages/historical.py",
    "ui/pages/about.py",
    "ui/pages/settings.py",
    "ui/pages/find_better.py",
    # Utils
    "utils/__init__.py",
    "utils/formatters.py",
    # Scripts
    "scripts/init_admins.py",
    "scripts/run_migrations.py",
    # Migrations
    "migrations/env.py",
    "migrations/script.py.mako",
    "migrations/versions/20241213_0001_initial_schema.py",
    "migrations/versions/20241214_0002_add_system_settings.py",
]

# Display columns for the data table
# Column groups for display
COLUMN_GROUPS = {
    'Identifiers': ['FUND_ID', 'FUND_NAME'],
    'Risk & Return': [
        'MONTHLY_YIELD', 'YEAR_TO_DATE_YIELD', 'AVG_ANNUAL_YIELD_TRAILING_1YR',
        'AVG_ANNUAL_YIELD_TRAILING_3YRS', 'AVG_ANNUAL_YIELD_TRAILING_5YRS',
        'SHARPE_RATIO', 'STANDARD_DEVIATION'
    ],
    'Exposure': [
        'TOTAL_ASSETS', 'STOCK_MARKET_EXPOSURE', 'FOREIGN_EXPOSURE',
        'FOREIGN_CURRENCY_EXPOSURE', 'LIQUID_ASSETS_PERCENT'
    ],
    'Fees': ['AVG_ANNUAL_MANAGEMENT_FEE', 'AVG_DEPOSIT_FEE'],
    'Other': ['FUND_CLASSIFICATION', 'ALPHA', 'NET_MONTHLY_DEPOSITS', 'INCEPTION_DATE'],
}

# Flattened display columns (order matters)
DISPLAY_COLUMNS = [
    # Identifiers
    'FUND_ID', 'FUND_NAME',
    # Risk & Return
    'MONTHLY_YIELD', 'YEAR_TO_DATE_YIELD', 'AVG_ANNUAL_YIELD_TRAILING_1YR',
    'AVG_ANNUAL_YIELD_TRAILING_3YRS', 'AVG_ANNUAL_YIELD_TRAILING_5YRS',
    'SHARPE_RATIO', 'STANDARD_DEVIATION',
    # Exposure
    'TOTAL_ASSETS', 'STOCK_MARKET_EXPOSURE', 'FOREIGN_EXPOSURE',
    'FOREIGN_CURRENCY_EXPOSURE', 'LIQUID_ASSETS_PERCENT',
    # Fees
    'AVG_ANNUAL_MANAGEMENT_FEE', 'AVG_DEPOSIT_FEE',
    # Other
    'FUND_CLASSIFICATION', 'ALPHA', 'NET_MONTHLY_DEPOSITS', 'INCEPTION_DATE',
]

# Column display labels (shortened)
COLUMN_LABELS = {
    # Identifiers
    'FUND_ID': 'Fund ID',
    'FUND_NAME': 'Fund Name',
    # Risk & Return (shortened)
    'MONTHLY_YIELD': '1M (%)',
    'YEAR_TO_DATE_YIELD': 'YTD (%)',
    'AVG_ANNUAL_YIELD_TRAILING_1YR': '1Y (%)',
    'AVG_ANNUAL_YIELD_TRAILING_3YRS': '3Y (%)',
    'AVG_ANNUAL_YIELD_TRAILING_5YRS': '5Y (%)',
    'SHARPE_RATIO': 'Sharpe',
    'STANDARD_DEVIATION': 'Std Dev',
    # Exposure (shortened)
    'TOTAL_ASSETS': 'Σ Assets (M)',
    'STOCK_MARKET_EXPOSURE': 'Stocks (%)',
    'FOREIGN_EXPOSURE': 'Foreign (%)',
    'FOREIGN_CURRENCY_EXPOSURE': 'Currency (%)',
    'LIQUID_ASSETS_PERCENT': 'Liquid (%)',
    # Fees
    'AVG_ANNUAL_MANAGEMENT_FEE': 'Mgmt (%)',
    'AVG_DEPOSIT_FEE': 'Deposit (%)',
    # Other
    'FUND_CLASSIFICATION': 'Sub-Product',
    'ALPHA': 'Alpha',
    'NET_MONTHLY_DEPOSITS': 'Net Deposits',
    'INCEPTION_DATE': 'Inception',
}

# Column group colors for header styling
COLUMN_GROUP_COLORS = {
    'Identifiers': '#1e3a5f',      # Dark blue
    'Risk & Return': '#1e5631',    # Dark green
    'Exposure': '#4a1e5f',         # Dark purple
    'Fees': '#5f3a1e',             # Dark orange/brown
    'Other': '#3a3a3a',            # Dark gray
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

