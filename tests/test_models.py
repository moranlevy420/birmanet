"""
Tests for models (dataset.py and database.py)
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from models.dataset import Dataset, SubFilter, PopulationFilter, DatasetRegistry
from models.database import User, Portfolio, PortfolioHolding, SystemSettings


class TestSubFilter:
    """Tests for SubFilter dataclass."""
    
    def test_create_sub_filter(self):
        """Test creating a SubFilter."""
        sub_filter = SubFilter(
            column="FUND_CLASSIFICATION",
            options=["Option A", "Option B"]
        )
        
        assert sub_filter.column == "FUND_CLASSIFICATION"
        assert len(sub_filter.options) == 2
        assert "Option A" in sub_filter.options
    
    def test_sub_filter_empty_options(self):
        """Test SubFilter with empty options."""
        sub_filter = SubFilter(
            column="TEST_COL",
            options=[]
        )
        
        assert sub_filter.options == []


class TestPopulationFilter:
    """Tests for PopulationFilter dataclass."""
    
    def test_create_population_filter(self):
        """Test creating a PopulationFilter."""
        pop_filter = PopulationFilter(
            column="TARGET_POPULATION",
            exclude_values=["Excluded1", "Excluded2"]
        )
        
        assert pop_filter.column == "TARGET_POPULATION"
        assert len(pop_filter.exclude_values) == 2


class TestDataset:
    """Tests for Dataset dataclass."""
    
    def test_create_dataset_minimal(self):
        """Test creating a Dataset with minimal fields."""
        dataset = Dataset(
            key="test",
            name="Test Dataset",
            name_heb="מוצר בדיקה",
            resource_ids=["res1", "res2"]
        )
        
        assert dataset.key == "test"
        assert dataset.name == "Test Dataset"
        assert dataset.name_heb == "מוצר בדיקה"
        assert len(dataset.resource_ids) == 2
        assert dataset.filter is None
        assert dataset.sub_filters is None
        assert dataset.population_filter is None
    
    def test_create_dataset_full(self):
        """Test creating a Dataset with all fields."""
        dataset = Dataset(
            key="full",
            name="Full Dataset",
            name_heb="מוצר מלא",
            resource_ids=["res1"],
            filter={"COL": ["val1", "val2"]},
            sub_filters=SubFilter(column="SUB_COL", options=["opt1"]),
            population_filter=PopulationFilter(column="POP", exclude_values=["exc"])
        )
        
        assert dataset.filter is not None
        assert dataset.sub_filters is not None
        assert dataset.population_filter is not None
    
    def test_from_dict_minimal(self):
        """Test creating Dataset from dictionary with minimal fields."""
        data = {
            "name": "Test",
            "name_heb": "בדיקה",
            "resource_ids": ["r1"]
        }
        
        dataset = Dataset.from_dict("test_key", data)
        
        assert dataset.key == "test_key"
        assert dataset.name == "Test"
        assert dataset.sub_filters is None
    
    def test_from_dict_with_sub_filters(self):
        """Test creating Dataset from dictionary with sub_filters."""
        data = {
            "name": "Test",
            "name_heb": "בדיקה",
            "resource_ids": ["r1"],
            "sub_filters": {
                "column": "CLASS",
                "options": ["A", "B", "C"]
            }
        }
        
        dataset = Dataset.from_dict("test_key", data)
        
        assert dataset.sub_filters is not None
        assert dataset.sub_filters.column == "CLASS"
        assert len(dataset.sub_filters.options) == 3
    
    def test_from_dict_with_population_filter(self):
        """Test creating Dataset from dictionary with population_filter."""
        data = {
            "name": "Test",
            "name_heb": "בדיקה",
            "resource_ids": ["r1"],
            "population_filter": {
                "column": "TARGET",
                "exclude_values": ["x", "y"]
            }
        }
        
        dataset = Dataset.from_dict("test_key", data)
        
        assert dataset.population_filter is not None
        assert dataset.population_filter.column == "TARGET"
        assert len(dataset.population_filter.exclude_values) == 2
    
    def test_from_dict_with_filter(self):
        """Test creating Dataset from dictionary with filter."""
        data = {
            "name": "Test",
            "name_heb": "בדיקה",
            "resource_ids": ["r1"],
            "filter": {
                "COL1": ["val1"],
                "COL2": ["val2", "val3"]
            }
        }
        
        dataset = Dataset.from_dict("test_key", data)
        
        assert dataset.filter is not None
        assert "COL1" in dataset.filter
        assert len(dataset.filter["COL2"]) == 2


class TestDatasetRegistry:
    """Tests for DatasetRegistry."""
    
    def test_load_from_file(self, sample_dataset_config):
        """Test loading registry from JSON file."""
        registry = DatasetRegistry(sample_dataset_config)
        
        assert len(registry) == 2
        assert "test_product" in registry.keys()
        assert "test_product_2" in registry.keys()
    
    def test_get_dataset(self, sample_dataset_config):
        """Test getting a dataset by key."""
        registry = DatasetRegistry(sample_dataset_config)
        
        dataset = registry.get("test_product")
        
        assert dataset is not None
        assert dataset.name == "Test Product"
    
    def test_get_nonexistent_dataset(self, sample_dataset_config):
        """Test getting nonexistent dataset."""
        registry = DatasetRegistry(sample_dataset_config)
        
        dataset = registry.get("nonexistent")
        
        assert dataset is None
    
    def test_list_all(self, sample_dataset_config):
        """Test listing all datasets."""
        registry = DatasetRegistry(sample_dataset_config)
        
        all_datasets = registry.list_all()
        
        assert len(all_datasets) == 2
        assert all(isinstance(d, Dataset) for d in all_datasets)
    
    def test_keys(self, sample_dataset_config):
        """Test getting all keys."""
        registry = DatasetRegistry(sample_dataset_config)
        
        keys = registry.keys()
        
        assert isinstance(keys, list)
        assert "test_product" in keys
    
    def test_iteration(self, sample_dataset_config):
        """Test iterating over registry."""
        registry = DatasetRegistry(sample_dataset_config)
        
        datasets = list(registry)
        
        assert len(datasets) == 2
    
    def test_len(self, sample_dataset_config):
        """Test registry length."""
        registry = DatasetRegistry(sample_dataset_config)
        
        assert len(registry) == 2
    
    def test_empty_config(self, temp_dir):
        """Test loading from empty config file."""
        config_path = temp_dir / "empty.json"
        with open(config_path, 'w') as f:
            json.dump({}, f)
        
        registry = DatasetRegistry(config_path)
        
        assert len(registry) == 0
    
    def test_nonexistent_file(self, temp_dir):
        """Test loading from nonexistent file."""
        registry = DatasetRegistry(temp_dir / "nonexistent.json")
        
        assert len(registry) == 0


class TestUserModel:
    """Tests for User SQLAlchemy model."""
    
    def test_user_creation(self, db_session):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            name="Test User",
            role="member"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.must_change_password is True
    
    def test_user_repr(self, db_session):
        """Test user string representation."""
        user = User(email="repr@example.com")
        db_session.add(user)
        db_session.commit()
        
        repr_str = repr(user)
        
        assert "User" in repr_str
        assert "repr@example.com" in repr_str
    
    def test_user_timestamps(self, db_session):
        """Test user timestamp fields."""
        user = User(email="time@example.com")
        db_session.add(user)
        db_session.commit()
        
        assert user.created_at is not None
        assert user.updated_at is not None


class TestPortfolioModel:
    """Tests for Portfolio SQLAlchemy model."""
    
    def test_portfolio_creation(self, db_session):
        """Test creating a portfolio."""
        user = User(email="portfolio@example.com")
        db_session.add(user)
        db_session.commit()
        
        portfolio = Portfolio(
            user_id=user.id,
            name="My Portfolio",
            description="Test portfolio"
        )
        db_session.add(portfolio)
        db_session.commit()
        
        assert portfolio.id is not None
        assert portfolio.user_id == user.id
    
    def test_portfolio_user_relationship(self, db_session):
        """Test portfolio-user relationship."""
        user = User(email="rel@example.com")
        db_session.add(user)
        db_session.commit()
        
        portfolio = Portfolio(user_id=user.id, name="Test")
        db_session.add(portfolio)
        db_session.commit()
        
        assert portfolio.user == user
        assert portfolio in user.portfolios


class TestSystemSettingsModel:
    """Tests for SystemSettings SQLAlchemy model."""
    
    def test_system_settings_creation(self, db_session):
        """Test creating system settings."""
        setting = SystemSettings(
            key="test_setting",
            value=1.5,
            min_value=0.0,
            max_value=10.0,
            default_value=1.0,
            description="A test setting"
        )
        db_session.add(setting)
        db_session.commit()
        
        assert setting.id is not None
        assert setting.key == "test_setting"
        assert setting.value == 1.5
    
    def test_system_settings_repr(self, db_session):
        """Test system settings string representation."""
        setting = SystemSettings(key="repr_test", value=2.0)
        db_session.add(setting)
        db_session.commit()
        
        repr_str = repr(setting)
        
        assert "SystemSettings" in repr_str
        assert "repr_test" in repr_str

