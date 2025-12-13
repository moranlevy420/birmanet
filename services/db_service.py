"""
Database service for managing SQLAlchemy connections and sessions.
"""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from models.database import Base

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Database service for managing connections and sessions.
    
    Supports:
    - SQLite for local development
    - PostgreSQL for production (via DATABASE_URL env var)
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database service.
        
        Args:
            database_url: Database connection URL. If not provided,
                         uses DATABASE_URL env var or defaults to SQLite.
        """
        self.database_url = database_url or self._get_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def _get_database_url(self) -> str:
        """Get database URL from environment or use default SQLite."""
        url = os.getenv("DATABASE_URL")
        
        if url:
            # Handle Heroku-style postgres:// URLs
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        
        # Default to SQLite in the app directory
        app_dir = Path(__file__).parent.parent
        db_path = app_dir / "app_data.db"
        return f"sqlite:///{db_path}"
    
    def _create_engine(self):
        """Create SQLAlchemy engine with appropriate settings."""
        if self.database_url.startswith("sqlite"):
            # SQLite-specific settings
            return create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true"
            )
        else:
            # PostgreSQL and other databases
            return create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true"
            )
    
    def create_tables(self) -> None:
        """Create all database tables. Use for initial setup only."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")
    
    def drop_tables(self) -> None:
        """Drop all database tables. Use with caution!"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("Database tables dropped")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session with automatic cleanup.
        
        Usage:
            with db_service.get_session() as session:
                user = session.query(User).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_instance(self) -> Session:
        """
        Get a session instance (caller must manage lifecycle).
        Prefer using get_session() context manager instead.
        """
        return self.SessionLocal()


# Global database service instance (lazy initialization)
_db_service: Optional[DatabaseService] = None


def get_db_service() -> DatabaseService:
    """Get or create the global database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


def init_db() -> None:
    """Initialize the database (create tables if they don't exist)."""
    db = get_db_service()
    db.create_tables()

