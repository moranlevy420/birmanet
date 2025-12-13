"""
Authentication UI components with persistent login via cookies.
"""

import streamlit as st
from typing import Optional
import extra_streamlit_components as stx

from services.auth_service import AuthService
from models.database import User

# Cookie settings
COOKIE_NAME = "fb_session"
COOKIE_EXPIRY_DAYS = 30


def get_cookie_manager():
    """Get the cookie manager instance."""
    return stx.CookieManager()


def render_login_form(auth_service: AuthService, cookie_manager) -> Optional[User]:
    """
    Render login form and handle authentication.
    
    Returns:
        User object if logged in, None otherwise
    """
    # Check for existing session cookie
    session_token = cookie_manager.get(COOKIE_NAME)
    if session_token:
        user = auth_service.validate_session(session_token)
        if user:
            st.session_state.user_email = user.email
            return user
    
    # Check session state (fallback for same-session)
    if st.session_state.get('user_email'):
        user = auth_service.get_user_by_email(st.session_state.user_email)
        if user and user.is_active:
            return user
    
    # Center the login form with compact width
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## 🔐 Login")
        st.markdown("Please log in to access the application.")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me", value=True)
            submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if not email or not password:
                st.error("Please enter both email and password")
                return None
            
            success, user, message = auth_service.authenticate(email.strip().lower(), password)
            
            if success:
                # Store email in session state
                st.session_state.user_email = user.email
                st.session_state.logged_in = True
                
                # Create persistent session if remember me is checked
                if remember_me:
                    token = auth_service.create_session(user)
                    cookie_manager.set(COOKIE_NAME, token, expires_at=None)
                
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    return None


def render_change_password_form(auth_service: AuthService, user_email: str) -> bool:
    """
    Render password change form.
    
    Returns:
        True if password was changed successfully
    """
    # Center the form with compact width
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## 🔑 Change Password")
        st.warning("You must change your password before continuing.")
        
        with st.form("change_password_form"):
            new_password = st.text_input("New Password", type="password", 
                                          help="Minimum 8 characters")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Change Password", use_container_width=True)
        
        if submit:
            if len(new_password) < 8:
                st.error("Password must be at least 8 characters")
                return False
            
            if new_password != confirm_password:
                st.error("Passwords do not match")
                return False
            
            # Get fresh user from database
            user = auth_service.get_user_by_email(user_email)
            if user and auth_service.change_password(user, new_password):
                st.success("Password changed successfully!")
                st.rerun()
                return True
            else:
                st.error("Failed to change password")
    
    return False


def render_user_menu(user: User, auth_service: AuthService, cookie_manager) -> None:
    """Render user menu in sidebar."""
    st.sidebar.markdown("---")
    
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        role_badge = "🔑" if user.role == 'admin' else "👤"
        st.markdown(f"{role_badge} **{user.name}**")
    with col2:
        if st.button("🚪", key="logout_btn", help="Logout"):
            # Invalidate session in database
            auth_service.invalidate_session(user)
            # Delete cookie
            cookie_manager.delete(COOKIE_NAME)
            # Clear session state
            st.session_state.user_email = None
            st.session_state.logged_in = False
            st.rerun()


def check_auth(auth_service: AuthService, cookie_manager) -> Optional[User]:
    """
    Check authentication status and render login if needed.
    
    Returns:
        User if authenticated, None otherwise (will show login form)
    """
    # First check for session cookie (persistent login)
    session_token = cookie_manager.get(COOKIE_NAME)
    if session_token:
        user = auth_service.validate_session(session_token)
        if user:
            st.session_state.user_email = user.email
            
            # Check if must change password
            if user.must_change_password:
                if not render_change_password_form(auth_service, user.email):
                    return None
            
            return user
    
    # Check session state for user email (same-session login)
    user_email = st.session_state.get('user_email')
    
    if not user_email:
        render_login_form(auth_service, cookie_manager)
        return None
    
    # Get fresh user from database
    db_user = auth_service.get_user_by_email(user_email)
    if not db_user or not db_user.is_active:
        st.session_state.user_email = None
        cookie_manager.delete(COOKIE_NAME)
        st.error("Session expired. Please log in again.")
        render_login_form(auth_service, cookie_manager)
        return None
    
    # Check if must change password
    if db_user.must_change_password:
        if not render_change_password_form(auth_service, user_email):
            return None
    
    return db_user


def is_admin(user: Optional[User]) -> bool:
    """Check if user is an admin."""
    return user is not None and user.role == 'admin'
