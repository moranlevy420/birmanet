"""
Authentication service for user login and session management.
"""

import bcrypt
import secrets
import string
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from models.database import User


class AuthService:
    """Handles user authentication and password management."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def generate_temp_password(length: int = 12) -> str:
        """Generate a secure temporary password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return self.db.query(User).filter(User.email == email).first()
    
    def authenticate(self, email: str, password: str) -> Tuple[bool, Optional[User], str]:
        """
        Authenticate a user.
        
        Returns:
            Tuple of (success, user, message)
        """
        user = self.get_user_by_email(email)
        
        if not user:
            return False, None, "Invalid email or password"
        
        if not user.is_active:
            return False, None, "Account is deactivated"
        
        if not user.password_hash:
            return False, None, "Password not set. Contact admin."
        
        if not self.verify_password(password, user.password_hash):
            return False, None, "Invalid email or password"
        
        return True, user, "Login successful"
    
    def change_password(self, user: User, new_password: str) -> bool:
        """Change user's password."""
        if len(new_password) < 8:
            return False
        
        user.password_hash = self.hash_password(new_password)
        user.must_change_password = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def create_user(
        self, 
        email: str, 
        name: str, 
        role: str = 'member',
        password: Optional[str] = None
    ) -> Tuple[User, str]:
        """
        Create a new user.
        
        Returns:
            Tuple of (user, temp_password)
        """
        # Generate temp password if not provided
        temp_password = password or self.generate_temp_password()
        
        user = User(
            email=email,
            name=name,
            role=role,
            password_hash=self.hash_password(temp_password),
            must_change_password=password is None,  # Force change if temp
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user, temp_password
    
    def update_user_role(self, user: User, new_role: str) -> bool:
        """Update user's role."""
        if new_role not in ('admin', 'member'):
            return False
        
        user.role = new_role
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def deactivate_user(self, user: User) -> bool:
        """Deactivate a user account."""
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def get_all_users(self):
        """Get all users."""
        return self.db.query(User).all()
    
    def reset_password(self, user: User) -> str:
        """Reset user's password to a new temporary one."""
        temp_password = self.generate_temp_password()
        user.password_hash = self.hash_password(temp_password)
        user.must_change_password = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return temp_password

