"""
Initialize admin users for the application.
Run this script once to set up initial admin accounts.

Usage:
    python scripts/init_admins.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.db_service import get_db_service, init_db
from services.auth_service import AuthService
from models.database import User


def create_initial_admins():
    """Create the initial admin users."""
    
    # Initialize database
    init_db()
    
    # Get database session
    db_service = get_db_service()
    
    # Admin users to create
    admins = [
        {
            "name": "Moran Levy",
            "email": "moran.levy.mail@gmail.com"
        },
        {
            "name": "Ido Birman", 
            "email": "ido.birman@echelon-fp.info"
        }
    ]
    
    with db_service.get_session() as session:
        auth_service = AuthService(session)
        
        print("=" * 50)
        print("  Find Better - Admin User Setup")
        print("=" * 50)
        print()
        
        for admin_info in admins:
            email = admin_info["email"].lower()
            name = admin_info["name"]
            
            # Check if user already exists
            existing = auth_service.get_user_by_email(email)
            
            if existing:
                # Reset password for existing user to ensure they can login
                temp_password = auth_service.reset_password(existing)
                print(f"🔄 Reset password for: {name}")
                print(f"   Email: {email}")
                print(f"   New Password: {temp_password}")
                print()
                print("   ⚠️  Save this password! User must change it on first login.")
                print()
                continue
            
            # Create admin user
            user, temp_password = auth_service.create_user(
                email=email,
                name=name,
                role="admin"
            )
            
            print(f"✅ Created admin: {name}")
            print(f"   Email: {email}")
            print(f"   Temporary Password: {temp_password}")
            print()
            print("   ⚠️  Save this password! User must change it on first login.")
            print()
        
        print("=" * 50)
        print("  Setup Complete!")
        print("=" * 50)


if __name__ == "__main__":
    create_initial_admins()

