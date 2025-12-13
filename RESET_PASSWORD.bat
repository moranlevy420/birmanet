@echo off
echo ========================================
echo    Find Better - Password Reset (Ido)
echo ========================================
echo.

echo Resetting password for Ido...
echo.

python -c "from services.db_service import get_db_service; from services.auth_service import AuthService; db=get_db_service(); s=db.get_session_instance(); a=AuthService(s); u=a.get_user_by_email('ido.birman@echelon-fp.info'); p=a.reset_password(u); print(''); print('New password for Ido:', p); print('')"

echo.
echo ========================================
echo    SAVE YOUR NEW PASSWORD ABOVE!
echo ========================================
echo.
pause

