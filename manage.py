#!/usr/bin/env python
"""
Database management CLI for Find Better.

Usage:
    python manage.py init      - Initialize database with current schema
    python manage.py migrate   - Run pending migrations
    python manage.py upgrade   - Alias for migrate
    python manage.py downgrade - Rollback last migration
    python manage.py reset     - Drop and recreate all tables (DANGER!)
    python manage.py status    - Show current migration status
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def run_alembic_command(command: str, *args) -> int:
    """Run an alembic command."""
    from alembic.config import Config
    from alembic import command as alembic_cmd
    
    # Get alembic.ini path
    config_path = Path(__file__).parent / "alembic.ini"
    alembic_cfg = Config(str(config_path))
    
    try:
        if command == "upgrade":
            revision = args[0] if args else "head"
            alembic_cmd.upgrade(alembic_cfg, revision)
        elif command == "downgrade":
            revision = args[0] if args else "-1"
            alembic_cmd.downgrade(alembic_cfg, revision)
        elif command == "current":
            alembic_cmd.current(alembic_cfg)
        elif command == "history":
            alembic_cmd.history(alembic_cfg)
        elif command == "revision":
            message = args[0] if args else "auto migration"
            alembic_cmd.revision(alembic_cfg, message=message, autogenerate=True)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def init_database():
    """Initialize database using migrations."""
    print("Initializing database...")
    # Use Alembic migrations to create tables
    result = run_alembic_command("upgrade", "head")
    if result == 0:
        print("✅ Database initialized successfully!")
    return result


def migrate():
    """Run pending migrations."""
    print("Running migrations...")
    result = run_alembic_command("upgrade", "head")
    if result == 0:
        print("✅ Migrations completed successfully!")
    return result


def downgrade(steps: str = "-1"):
    """Rollback migrations."""
    print(f"Rolling back migrations ({steps})...")
    result = run_alembic_command("downgrade", steps)
    if result == 0:
        print("✅ Rollback completed successfully!")
    return result


def reset_database():
    """Drop and recreate all tables."""
    confirm = input("⚠️  This will DELETE ALL DATA! Are you sure? (type 'yes'): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return 1
    
    print("Resetting database...")
    from services.db_service import get_db_service
    db = get_db_service()
    db.drop_tables()
    db.create_tables()
    print("✅ Database reset successfully!")
    return 0


def show_status():
    """Show current migration status."""
    print("Current migration status:")
    print("-" * 40)
    run_alembic_command("current")
    print("\nMigration history:")
    print("-" * 40)
    run_alembic_command("history")


def create_migration(message: str = None):
    """Create a new migration based on model changes."""
    if not message:
        message = input("Enter migration message: ")
    print(f"Creating migration: {message}")
    return run_alembic_command("revision", message)


def print_help():
    """Print usage help."""
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1].lower()
    args = sys.argv[2:]
    
    commands = {
        "init": init_database,
        "migrate": migrate,
        "upgrade": migrate,
        "downgrade": lambda: downgrade(args[0] if args else "-1"),
        "reset": reset_database,
        "status": show_status,
        "revision": lambda: create_migration(args[0] if args else None),
        "help": print_help,
        "--help": print_help,
        "-h": print_help,
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        print_help()
        return 1
    
    result = commands[command]()
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    sys.exit(main())

