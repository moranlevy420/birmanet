"""
Cache service for storing and retrieving data.
Currently uses SQLite, but designed to be swappable for Redis in cloud deployment.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseCacheService(ABC):
    """Abstract base class for cache services."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[pd.DataFrame]:
        """Retrieve data from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, data: pd.DataFrame) -> None:
        """Store data in cache."""
        pass
    
    @abstractmethod
    def get_age_hours(self, key: str) -> Optional[float]:
        """Get age of cached data in hours."""
        pass
    
    @abstractmethod
    def clear(self, key: str) -> None:
        """Clear cached data for a key."""
        pass
    
    @abstractmethod
    def is_valid(self, key: str, max_age_hours: float) -> bool:
        """Check if cached data is still valid."""
        pass


class SQLiteCacheService(BaseCacheService):
    """SQLite-based cache service for local deployment."""
    
    def __init__(self, cache_dir: Path, max_age_hours: float = 24):
        self.cache_dir = cache_dir
        self.max_age_hours = max_age_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_db_path(self, key: str) -> Path:
        """Get database path for a cache key."""
        return self.cache_dir / f"{key}_cache.db"
    
    def _get_connection(self, key: str) -> sqlite3.Connection:
        """Get database connection."""
        db_path = self._get_db_path(key)
        return sqlite3.connect(db_path)
    
    def get(self, key: str) -> Optional[pd.DataFrame]:
        """Retrieve data from SQLite cache."""
        db_path = self._get_db_path(key)
        if not db_path.exists():
            return None
        
        try:
            conn = self._get_connection(key)
            df = pd.read_sql_query("SELECT * FROM fund_data", conn)
            conn.close()
            
            # Convert REPORT_DATE back to datetime
            if 'REPORT_DATE' in df.columns:
                df['REPORT_DATE'] = pd.to_datetime(df['REPORT_DATE'])
            
            return df
        except Exception as e:
            logger.error(f"Error loading from cache: {e}")
            return None
    
    def set(self, key: str, data: pd.DataFrame) -> None:
        """Store data in SQLite cache."""
        try:
            conn = self._get_connection(key)
            
            # Store the data
            data.to_sql('fund_data', conn, if_exists='replace', index=False)
            
            # Store metadata
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    timestamp TEXT
                )
            """)
            conn.execute("""
                INSERT OR REPLACE INTO cache_metadata (key, timestamp) 
                VALUES (?, ?)
            """, (key, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(data)} records to cache for {key}")
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
    
    def get_age_hours(self, key: str) -> Optional[float]:
        """Get age of cached data in hours."""
        db_path = self._get_db_path(key)
        if not db_path.exists():
            return None
        
        try:
            conn = self._get_connection(key)
            cursor = conn.execute(
                "SELECT timestamp FROM cache_metadata WHERE key = ?", 
                (key,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                cached_time = datetime.fromisoformat(row[0])
                age = datetime.now() - cached_time
                return age.total_seconds() / 3600
            return None
        except Exception:
            return None
    
    def is_valid(self, key: str, max_age_hours: Optional[float] = None) -> bool:
        """Check if cached data is still valid."""
        max_age = max_age_hours or self.max_age_hours
        age = self.get_age_hours(key)
        if age is None:
            return False
        return age < max_age
    
    def clear(self, key: str) -> None:
        """Clear cached data for a key."""
        db_path = self._get_db_path(key)
        if db_path.exists():
            db_path.unlink()
            logger.info(f"Cleared cache for {key}")


# Future: Redis cache service for cloud deployment
# class RedisCacheService(BaseCacheService):
#     def __init__(self, redis_url: str, max_age_hours: float = 24):
#         self.redis = redis.from_url(redis_url)
#         self.max_age_hours = max_age_hours
#     ...

