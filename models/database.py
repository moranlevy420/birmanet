"""
SQLAlchemy database models for persistent data.
These models are for user data that requires migrations.
(Cache data is stored separately in cache_service.py)
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class User(Base):
    """User account model."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=True)  # Bcrypt hashed password
    role = Column(String(50), default='member')  # 'admin' or 'member'
    must_change_password = Column(Boolean, default=True)  # Force password change on first login
    session_token = Column(String(255), nullable=True, index=True)  # For persistent login
    session_expires = Column(DateTime, nullable=True)  # Session expiry time
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("FavoriteFund", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Portfolio(Base):
    """User portfolio model - tracks user's fund investments."""
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}')>"


class PortfolioHolding(Base):
    """Individual fund holding within a portfolio."""
    __tablename__ = 'portfolio_holdings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False, index=True)
    fund_id = Column(Integer, nullable=False, index=True)  # References external fund data
    fund_name = Column(String(500), nullable=True)  # Cached for display
    amount = Column(Float, nullable=True)  # Investment amount
    units = Column(Float, nullable=True)  # Number of units
    purchase_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    
    def __repr__(self):
        return f"<PortfolioHolding(id={self.id}, fund_id={self.fund_id})>"


class FavoriteFund(Base):
    """User's favorite/starred funds."""
    __tablename__ = 'favorite_funds'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    fund_id = Column(Integer, nullable=False, index=True)
    fund_name = Column(String(500), nullable=True)  # Cached for display
    dataset_type = Column(String(50), nullable=True)  # pension, gemel, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    
    def __repr__(self):
        return f"<FavoriteFund(user_id={self.user_id}, fund_id={self.fund_id})>"


class UserPreference(Base):
    """User preferences and settings."""
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, key='{self.key}')>"


class SavedComparison(Base):
    """Saved fund comparisons."""
    __tablename__ = 'saved_comparisons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    fund_ids = Column(JSON, nullable=False)  # List of fund IDs
    dataset_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SavedComparison(id={self.id}, name='{self.name}')>"


class AlertRule(Base):
    """User alert rules for fund monitoring."""
    __tablename__ = 'alert_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    fund_id = Column(Integer, nullable=False, index=True)
    metric = Column(String(100), nullable=False)  # e.g., 'MONTHLY_YIELD', 'TOTAL_ASSETS'
    operator = Column(String(20), nullable=False)  # 'gt', 'lt', 'eq', 'gte', 'lte'
    threshold = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AlertRule(id={self.id}, fund_id={self.fund_id}, metric='{self.metric}')>"


class SystemSettings(Base):
    """System-wide settings configurable by admin."""
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    default_value = Column(Float, nullable=True)
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    def __repr__(self):
        return f"<SystemSettings(key='{self.key}', value={self.value})>"


# Default threshold settings for Find Better feature
DEFAULT_THRESHOLDS = {
    'yield_threshold': {
        'min': 0.0,
        'max': 5.0,
        'default': 0.1,
        'description': 'Minimum yield improvement (%) for a fund to be considered "better"'
    },
    'std_threshold': {
        'min': 0.0,
        'max': 15.0,
        'default': 0.0,
        'description': 'Required reduction in standard deviation (%) below user fund'
    },
    'stock_exposure_threshold': {
        'min': 0.0,
        'max': 20.0,
        'default': 5.0,
        'description': 'Tolerance (%) for stock market exposure difference'
    },
    'foreign_exposure_threshold': {
        'min': 0.0,
        'max': 20.0,
        'default': 5.0,
        'description': 'Tolerance (%) for foreign exposure difference'
    },
    'currency_exposure_threshold': {
        'min': 0.0,
        'max': 20.0,
        'default': 5.0,
        'description': 'Tolerance (%) for currency exposure difference'
    },
    'liquidity_threshold': {
        'min': 0.0,
        'max': 20.0,
        'default': 5.0,
        'description': 'Tolerance (%) for liquid assets difference'
    }
}

