"""
Authentication UI components.
"""

import streamlit as st
from typing import Optional

from services.auth_service import AuthService
from models.database import User


def render_login_form(auth_service: AuthService) -> Optional[User]:
    """
    Render login form and handle authentication.
    
    Returns:
        User object if logged in, None otherwise
    """
    # Check if already logged in (by email stored in session)
    if st.session_state.get('user_email'):
        user = auth_service.get_user_by_email(st.session_state.user_email)
        if user and user.is_active:
            return user
    
    st.markdown("## 🔐 Login")
    st.markdown("Please log in to access the application.")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="your.email@example.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if not email or not password:
                st.error("Please enter both email and password")
                return None
            
            success, user, message = auth_service.authenticate(email.strip().lower(), password)
            
            if success:
                # Store only the email in session state (not the ORM object)
                st.session_state.user_email = user.email
                st.session_state.logged_in = True
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


def render_user_menu(user: User) -> None:
    """Render user menu in sidebar."""
    st.sidebar.markdown("---")
    
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        role_badge = "🔑" if user.role == 'admin' else "👤"
        st.markdown(f"{role_badge} **{user.name}**")
    with col2:
        if st.button("🚪", key="logout_btn", help="Logout"):
            st.session_state.user_email = None
            st.session_state.logged_in = False
            st.rerun()


def check_auth(auth_service: AuthService) -> Optional[User]:
    """
    Check authentication status and render login if needed.
    
    Returns:
        User if authenticated, None otherwise (will show login form)
    """
    # Check session state for user email
    user_email = st.session_state.get('user_email')
    
    if not user_email:
        render_login_form(auth_service)
        return None
    
    # Get fresh user from database
    db_user = auth_service.get_user_by_email(user_email)
    if not db_user or not db_user.is_active:
        st.session_state.user_email = None
        st.error("Session expired. Please log in again.")
        render_login_form(auth_service)
        return None
    
    # Check if must change password
    if db_user.must_change_password:
        if not render_change_password_form(auth_service, user_email):
            return None
    
    return db_user


def is_admin(user: Optional[User]) -> bool:
    """Check if user is an admin."""
    return user is not None and user.role == 'admin'
