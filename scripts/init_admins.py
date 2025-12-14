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
    
    created_users = []
    
    with db_service.get_session() as session:
        auth_service = AuthService(session)
        
        print()
        print("=" * 60)
        print("       FIND BETTER - Admin User Setup")
        print("=" * 60)
        print()
        
        for admin_info in admins:
            email = admin_info["email"].lower()
            name = admin_info["name"]
            
            # Check if user already exists
            existing = auth_service.get_user_by_email(email)
            
            if existing:
                # Reset password for existing admin
                temp_password = auth_service.reset_password(email)
                if temp_password:
                    created_users.append({
                        "name": name,
                        "email": email,
                        "password": temp_password,
                        "status": "Password Reset"
                    })
                    print(f"  [OK] {name} - password reset")
                else:
                    print(f"  [!] {name} - could not reset password")
            else:
                # Create new admin user
                user, temp_password = auth_service.create_user(
                    email=email,
                    name=name,
                    role="admin"
                )
                created_users.append({
                    "name": name,
                    "email": email,
                    "password": temp_password,
                    "status": "Created"
                })
                print(f"  [OK] {name} - account created")
        
        print()
        
        # Show prominent password display
        if created_users:
            print("=" * 60)
            print()
            print("  **************************************************")
            print("  *                                                *")
            print("  *          SAVE THESE PASSWORDS NOW!             *")
            print("  *                                                *")
            print("  **************************************************")
            print()
            
            for user_info in created_users:
                print(f"  User: {user_info['name']}")
                print(f"  Email: {user_info['email']}")
                print()
                print(f"  +------------------------------------------+")
                print(f"  |  PASSWORD:  {user_info['password']:<28} |")
                print(f"  +------------------------------------------+")
                print()
                print(f"  (You must change this password on first login)")
                print()
                print("-" * 60)
                print()
        
        print("=" * 60)
        print("       Setup Complete! You can now run the app.")
        print("=" * 60)
        print()


if __name__ == "__main__":
    create_initial_admins()
