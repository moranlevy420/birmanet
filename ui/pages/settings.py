"""
Settings page - Admin and user settings.
"""

import streamlit as st
from typing import Optional

from models.database import User
from services.auth_service import AuthService


def render_admin_settings(auth_service: AuthService, current_user: User) -> None:
    """Render admin settings tab."""
    st.subheader("⚙️ Admin Settings")
    
    # User Management
    st.markdown("### 👥 User Management")
    
    users = auth_service.get_all_users()
    
    # Display users table
    if users:
        user_data = []
        for u in users:
            user_data.append({
                "ID": u.id,
                "Name": u.name,
                "Email": u.email,
                "Role": u.role,
                "Active": "✅" if u.is_active else "❌",
                "Must Change PW": "⚠️" if u.must_change_password else "✓"
            })
        st.dataframe(user_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Add new user
    with st.expander("➕ Add New User"):
        with st.form("add_user_form"):
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email")
            new_role = st.selectbox("Role", ["member", "admin"])
            
            if st.form_submit_button("Create User"):
                if new_name and new_email:
                    try:
                        user, temp_pw = auth_service.create_user(
                            email=new_email.strip().lower(),
                            name=new_name.strip(),
                            role=new_role
                        )
                        st.success(f"User created! Temporary password: `{temp_pw}`")
                        st.warning("Share this password securely. User must change it on first login.")
                    except Exception as e:
                        st.error(f"Error creating user: {e}")
                else:
                    st.error("Please fill in all fields")
    
    # Reset user password
    with st.expander("🔑 Reset User Password"):
        user_emails = [u.email for u in users if u.id != current_user.id]
        if user_emails:
            selected_email = st.selectbox("Select User", user_emails)
            if st.button("Reset Password"):
                user = auth_service.get_user_by_email(selected_email)
                if user:
                    temp_pw = auth_service.reset_password(user)
                    st.success(f"Password reset! New temporary password: `{temp_pw}`")
                    st.warning("Share this password securely.")
        else:
            st.info("No other users to manage")
    
    # Change user role
    with st.expander("🔄 Change User Role"):
        user_emails = [u.email for u in users if u.id != current_user.id]
        if user_emails:
            selected_email = st.selectbox("Select User", user_emails, key="role_user")
            new_role = st.selectbox("New Role", ["member", "admin"], key="new_role")
            if st.button("Update Role"):
                user = auth_service.get_user_by_email(selected_email)
                if user:
                    auth_service.update_user_role(user, new_role)
                    st.success(f"Role updated to {new_role}")
                    st.rerun()
        else:
            st.info("No other users to manage")
    
    # Deactivate user
    with st.expander("🚫 Deactivate User"):
        active_users = [u.email for u in users if u.is_active and u.id != current_user.id]
        if active_users:
            selected_email = st.selectbox("Select User", active_users, key="deact_user")
            if st.button("Deactivate", type="primary"):
                user = auth_service.get_user_by_email(selected_email)
                if user:
                    auth_service.deactivate_user(user)
                    st.success("User deactivated")
                    st.rerun()
        else:
            st.info("No other active users")


def render_user_settings(auth_service: AuthService, current_user: User) -> None:
    """Render user settings (for non-admins or personal settings)."""
    st.subheader("👤 My Settings")
    
    # Profile info
    st.markdown("### 📋 Profile")
    st.write(f"**Name:** {current_user.name}")
    st.write(f"**Email:** {current_user.email}")
    st.write(f"**Role:** {current_user.role.title()}")
    
    st.markdown("---")
    
    # Change own password
    st.markdown("### 🔑 Change Password")
    with st.form("change_own_password"):
        current_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password", help="Minimum 8 characters")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Update Password"):
            # Verify current password
            success, _, _ = auth_service.authenticate(current_user.email, current_pw)
            if not success:
                st.error("Current password is incorrect")
            elif len(new_pw) < 8:
                st.error("New password must be at least 8 characters")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match")
            else:
                if auth_service.change_password(current_user, new_pw):
                    st.success("Password changed successfully!")
                else:
                    st.error("Failed to change password")


def render_settings(auth_service: AuthService, current_user: User) -> None:
    """Render the settings page with tabs for admin/user settings."""
    
    if current_user.role == 'admin':
        # Admins see both admin settings and personal settings
        tab1, tab2 = st.tabs(["⚙️ Admin Settings", "👤 My Settings"])
        
        with tab1:
            render_admin_settings(auth_service, current_user)
        
        with tab2:
            render_user_settings(auth_service, current_user)
    else:
        # Regular users only see their own settings
        render_user_settings(auth_service, current_user)

