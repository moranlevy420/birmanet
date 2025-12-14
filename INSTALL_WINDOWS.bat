@echo off
echo ========================================
echo    Find Better - First Time Install
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python first:
    echo   1. Go to: https://www.python.org/downloads/
    echo   2. Download Python 3.9 or higher
    echo   3. IMPORTANT: Check "Add Python to PATH" during install
    echo   4. Run this script again
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Install dependencies
echo Installing Python packages...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed
echo.

REM Run database migrations
echo Setting up database...
python scripts/run_migrations.py

echo.
echo ========================================
echo    Setting up admin accounts...
echo ========================================
echo.
python scripts/init_admins.py

echo.
echo ========================================
echo    INSTALLATION COMPLETE!
echo ========================================
echo.
echo    IMPORTANT: Save the password shown above!
echo.
echo    To start the app: double-click run_app.bat
echo.
echo ========================================
echo.
pause
