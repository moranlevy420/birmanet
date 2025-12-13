"""
Tests for services/auth_service.py
"""

import pytest
from datetime import datetime, timedelta

from services.auth_service import AuthService


class TestPasswordHashing:
    """Tests for password hashing functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "SecurePass123"
        hashed = AuthService.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are long
        assert hashed.startswith("$2")  # Bcrypt prefix
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "SecurePass123"
        hashed = AuthService.hash_password(password)
        
        assert AuthService.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "SecurePass123"
        wrong_password = "WrongPass456"
        hashed = AuthService.hash_password(password)
        
        assert AuthService.verify_password(wrong_password, hashed) is False
    
    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        assert AuthService.verify_password("password", "invalid_hash") is False
    
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salting)."""
        password = "SecurePass123"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)
        
        assert hash1 != hash2  # Different salts
        assert AuthService.verify_password(password, hash1) is True
        assert AuthService.verify_password(password, hash2) is True


class TestGenerateTempPassword:
    """Tests for temporary password generation."""
    
    def test_default_length(self):
        """Test default password length."""
        password = AuthService.generate_temp_password()
        assert len(password) == 12
    
    def test_custom_length(self):
        """Test custom password length."""
        password = AuthService.generate_temp_password(length=20)
        assert len(password) == 20
    
    def test_alphanumeric_only(self):
        """Test that password contains only alphanumeric characters."""
        password = AuthService.generate_temp_password()
        assert password.isalnum()
    
    def test_unique_passwords(self):
        """Test that generated passwords are unique."""
        passwords = [AuthService.generate_temp_password() for _ in range(100)]
        assert len(set(passwords)) == 100


class TestUserAuthentication:
    """Tests for user authentication."""
    
    def test_authenticate_success(self, auth_service, sample_user):
        """Test successful authentication."""
        user, password = sample_user
        
        success, auth_user, message = auth_service.authenticate(user.email, password)
        
        assert success is True
        assert auth_user is not None
        assert auth_user.id == user.id
        assert message == "Login successful"
    
    def test_authenticate_wrong_password(self, auth_service, sample_user):
        """Test authentication with wrong password."""
        user, _ = sample_user
        
        success, auth_user, message = auth_service.authenticate(user.email, "WrongPass")
        
        assert success is False
        assert auth_user is None
        assert "Invalid" in message
    
    def test_authenticate_nonexistent_user(self, auth_service):
        """Test authentication with nonexistent user."""
        success, auth_user, message = auth_service.authenticate(
            "nonexistent@example.com", "password"
        )
        
        assert success is False
        assert auth_user is None
    
    def test_authenticate_inactive_user(self, auth_service, sample_user):
        """Test authentication with inactive user."""
        user, password = sample_user
        auth_service.deactivate_user(user)
        
        success, auth_user, message = auth_service.authenticate(user.email, password)
        
        assert success is False
        assert "deactivated" in message.lower()


class TestUserCreation:
    """Tests for user creation."""
    
    def test_create_user_with_password(self, auth_service):
        """Test creating user with specified password."""
        user, temp_password = auth_service.create_user(
            email="new@example.com",
            name="New User",
            role="member",
            password="MyPassword123"
        )
        
        assert user is not None
        assert user.email == "new@example.com"
        assert user.name == "New User"
        assert user.role == "member"
        assert user.must_change_password is False  # Explicit password
        assert temp_password == "MyPassword123"
    
    def test_create_user_without_password(self, auth_service):
        """Test creating user without password (temp password generated)."""
        user, temp_password = auth_service.create_user(
            email="temp@example.com",
            name="Temp User",
            role="admin"
        )
        
        assert user is not None
        assert user.must_change_password is True  # Needs to change temp password
        assert len(temp_password) == 12
        
        # Should be able to authenticate with temp password
        success, _, _ = auth_service.authenticate("temp@example.com", temp_password)
        assert success is True
    
    def test_create_admin_user(self, auth_service):
        """Test creating admin user."""
        user, _ = auth_service.create_user(
            email="admin2@example.com",
            name="Admin",
            role="admin",
            password="AdminPass"
        )
        
        assert user.role == "admin"


class TestPasswordChange:
    """Tests for password change functionality."""
    
    def test_change_password_success(self, auth_service, sample_user):
        """Test successful password change."""
        user, old_password = sample_user
        new_password = "NewSecurePass456"
        
        result = auth_service.change_password(user, new_password)
        
        assert result is True
        assert user.must_change_password is False
        
        # Old password should not work
        success, _, _ = auth_service.authenticate(user.email, old_password)
        assert success is False
        
        # New password should work
        success, _, _ = auth_service.authenticate(user.email, new_password)
        assert success is True
    
    def test_change_password_too_short(self, auth_service, sample_user):
        """Test password change with too short password."""
        user, _ = sample_user
        
        result = auth_service.change_password(user, "short")
        
        assert result is False  # Should fail for password < 8 chars


class TestResetPassword:
    """Tests for password reset functionality."""
    
    def test_reset_password(self, auth_service, sample_user):
        """Test password reset."""
        user, old_password = sample_user
        
        new_temp_password = auth_service.reset_password(user)
        
        assert len(new_temp_password) == 12
        assert user.must_change_password is True
        
        # Old password should not work
        success, _, _ = auth_service.authenticate(user.email, old_password)
        assert success is False
        
        # New temp password should work
        success, _, _ = auth_service.authenticate(user.email, new_temp_password)
        assert success is True


class TestUserRoles:
    """Tests for user role management."""
    
    def test_update_role_to_admin(self, auth_service, sample_user):
        """Test updating user role to admin."""
        user, _ = sample_user
        assert user.role == "member"
        
        result = auth_service.update_user_role(user, "admin")
        
        assert result is True
        assert user.role == "admin"
    
    def test_update_role_to_member(self, auth_service, admin_user):
        """Test updating user role to member."""
        user, _ = admin_user
        assert user.role == "admin"
        
        result = auth_service.update_user_role(user, "member")
        
        assert result is True
        assert user.role == "member"
    
    def test_update_role_invalid(self, auth_service, sample_user):
        """Test updating user role to invalid role."""
        user, _ = sample_user
        
        result = auth_service.update_user_role(user, "superadmin")
        
        assert result is False
        assert user.role == "member"  # Unchanged


class TestSessionManagement:
    """Tests for session token management."""
    
    def test_generate_session_token(self):
        """Test session token generation."""
        token = AuthService.generate_session_token()
        
        assert len(token) > 30
        # Should be URL-safe base64
        assert all(c.isalnum() or c in '-_' for c in token)
    
    def test_create_session(self, auth_service, sample_user):
        """Test session creation."""
        user, _ = sample_user
        
        token = auth_service.create_session(user)
        
        assert token is not None
        assert user.session_token == token
        assert user.session_expires is not None
        assert user.session_expires > datetime.utcnow()
    
    def test_validate_session_valid(self, auth_service, sample_user):
        """Test validation of valid session."""
        user, _ = sample_user
        token = auth_service.create_session(user)
        
        validated_user = auth_service.validate_session(token)
        
        assert validated_user is not None
        assert validated_user.id == user.id
    
    def test_validate_session_invalid_token(self, auth_service):
        """Test validation of invalid token."""
        validated_user = auth_service.validate_session("invalid_token_xyz")
        
        assert validated_user is None
    
    def test_validate_session_empty_token(self, auth_service):
        """Test validation of empty token."""
        validated_user = auth_service.validate_session("")
        
        assert validated_user is None
    
    def test_validate_session_none_token(self, auth_service):
        """Test validation of None token."""
        validated_user = auth_service.validate_session(None)
        
        assert validated_user is None
    
    def test_invalidate_session(self, auth_service, sample_user):
        """Test session invalidation (logout)."""
        user, _ = sample_user
        token = auth_service.create_session(user)
        
        auth_service.invalidate_session(user)
        
        assert user.session_token is None
        assert user.session_expires is None
        
        # Token should no longer be valid
        validated_user = auth_service.validate_session(token)
        assert validated_user is None


class TestGetAllUsers:
    """Tests for getting all users."""
    
    def test_get_all_users(self, auth_service, sample_user, admin_user):
        """Test getting all users."""
        users = auth_service.get_all_users()
        
        assert len(users) >= 2
        emails = [u.email for u in users]
        assert "test@example.com" in emails
        assert "admin@example.com" in emails
    
    def test_get_all_users_empty(self, auth_service):
        """Test getting users when none exist."""
        users = auth_service.get_all_users()
        
        assert isinstance(users, list)


class TestDeactivateUser:
    """Tests for user deactivation."""
    
    def test_deactivate_user(self, auth_service, sample_user):
        """Test deactivating a user."""
        user, password = sample_user
        assert user.is_active is True
        
        result = auth_service.deactivate_user(user)
        
        assert result is True
        assert user.is_active is False
        
        # Should not be able to authenticate
        success, _, _ = auth_service.authenticate(user.email, password)
        assert success is False

