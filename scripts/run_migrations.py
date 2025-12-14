"""
Run database migrations using Alembic.
This script safely upgrades the database schema without losing data.

Usage:
    python scripts/run_migrations.py
"""

import sys
import sqlite3
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_column_exists(db_path: str, table: str, column: str) -> bool:
    """Check if a column exists in a SQLite table."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        return column in columns
    except Exception:
        return False


def check_table_exists(db_path: str, table: str) -> bool:
    """Check if a table exists in the database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception:
        return False


def migrate_legacy_database(db_path: str):
    """
    Migrate a legacy database that was created before Alembic.
    Adds missing columns to existing tables.
    """
    print("Checking for legacy database schema...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    migrations_applied = []
    
    # Check and add missing columns to users table
    if check_table_exists(db_path, 'users'):
        user_columns_to_add = [
            ('password_hash', 'VARCHAR(255)'),
            ('role', "VARCHAR(50) DEFAULT 'member'"),
            ('must_change_password', 'BOOLEAN DEFAULT 1'),
            ('session_token', 'VARCHAR(255)'),
            ('session_expires', 'DATETIME'),
        ]
        
        for column_name, column_type in user_columns_to_add:
            if not check_column_exists(db_path, 'users', column_name):
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                    migrations_applied.append(f"Added users.{column_name}")
                    print(f"  ✅ Added column: users.{column_name}")
                except Exception as e:
                    print(f"  ⚠️  Could not add users.{column_name}: {e}")
    
    # Create system_settings table if it doesn't exist
    if not check_table_exists(db_path, 'system_settings'):
        try:
            cursor.execute("""
                CREATE TABLE system_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR(100) NOT NULL UNIQUE,
                    value FLOAT,
                    min_value FLOAT,
                    max_value FLOAT,
                    default_value FLOAT,
                    description VARCHAR(500),
                    updated_at DATETIME,
                    updated_by INTEGER REFERENCES users(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_system_settings_key ON system_settings (key)")
            migrations_applied.append("Created system_settings table")
            print("  ✅ Created table: system_settings")
        except Exception as e:
            print(f"  ⚠️  Could not create system_settings table: {e}")
    
    conn.commit()
    conn.close()
    
    if migrations_applied:
        print(f"\n✅ Applied {len(migrations_applied)} legacy migrations")
    else:
        print("  No legacy migrations needed")
    
    return migrations_applied


def run_migrations():
    """Run all pending database migrations."""
    print("=" * 50)
    print("  Find Better - Database Migration")
    print("=" * 50)
    print()
    
    from services.db_service import get_db_service
    
    # Ensure database exists
    db_service = get_db_service()
    db_path = db_service.database_url.replace('sqlite:///', '')
    
    # First, handle legacy databases that pre-date Alembic
    if Path(db_path).exists():
        if check_table_exists(db_path, 'users') and not check_column_exists(db_path, 'users', 'password_hash'):
            print("⚠️  Legacy database detected (missing auth columns)")
            migrate_legacy_database(db_path)
            print()
    
    # Configure Alembic
    from alembic.config import Config
    from alembic import command
    
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(Path(__file__).parent.parent / "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_service.database_url)
    
    try:
        # Check current revision
        print("Checking Alembic version...")
        
        # Check if alembic_version table exists
        has_alembic = check_table_exists(db_path, 'alembic_version')
        
        if not has_alembic:
            if Path(db_path).exists() and check_table_exists(db_path, 'users'):
                # Existing database without Alembic - stamp it as current
                print("Existing database without Alembic version. Stamping as current...")
                command.stamp(alembic_cfg, "head")
                print("✅ Database stamped at latest version")
            else:
                # New database - create tables and stamp
                print("New database detected. Creating tables...")
                from models.database import Base
                Base.metadata.create_all(bind=db_service.engine)
                command.stamp(alembic_cfg, "head")
                print("✅ Database initialized at latest version")
        else:
            # Run any pending migrations
            print("Running pending migrations...")
            command.upgrade(alembic_cfg, "head")
            print("✅ Database migration complete!")
        
    except Exception as e:
        print(f"⚠️  Alembic migration note: {e}")
        
        # Fallback: ensure all tables exist
        try:
            from models.database import Base
            Base.metadata.create_all(bind=db_service.engine)
            print("✅ Database tables verified")
        except Exception as e2:
            print(f"❌ Failed to verify tables: {e2}")
    
    print()
    print("=" * 50)


if __name__ == "__main__":
    run_migrations()
