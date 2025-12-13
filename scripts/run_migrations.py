"""
Run database migrations using Alembic.
This script safely upgrades the database schema without losing data.

Usage:
    python scripts/run_migrations.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command
from services.db_service import get_db_service


def run_migrations():
    """Run all pending database migrations."""
    print("=" * 50)
    print("  Find Better - Database Migration")
    print("=" * 50)
    print()
    
    # Ensure database exists
    db_service = get_db_service()
    
    # Configure Alembic
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(Path(__file__).parent.parent / "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_service.database_url)
    
    try:
        # Check current revision
        print("Checking current database version...")
        
        # Stamp the database if it's new (no alembic_version table)
        try:
            command.current(alembic_cfg)
        except Exception:
            print("New database detected. Stamping with base revision...")
            # Create tables first
            from models.database import Base
            Base.metadata.create_all(bind=db_service.engine)
            command.stamp(alembic_cfg, "head")
            print("✅ Database initialized at latest version")
            return
        
        # Run pending migrations
        print("Running pending migrations...")
        command.upgrade(alembic_cfg, "head")
        print()
        print("✅ Database migration complete!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        print()
        print("If this is a fresh install, the database will be created automatically.")
        
        # Fallback: create tables directly
        try:
            from models.database import Base
            Base.metadata.create_all(bind=db_service.engine)
            print("✅ Database tables created")
        except Exception as e2:
            print(f"❌ Failed to create tables: {e2}")
    
    print()
    print("=" * 50)


if __name__ == "__main__":
    run_migrations()

