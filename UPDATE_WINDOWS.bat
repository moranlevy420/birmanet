@echo off
echo ========================================
echo    Find Better - Update from GitHub
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python first.
    pause
    exit /b 1
)

REM Create directories if they don't exist
if not exist "scripts" mkdir scripts

REM Check if download script exists, if not download it first
if not exist "scripts\download_update.py" (
    echo First-time setup: downloading update script...
    echo.
    echo You need a GitHub token to access the private repository.
    echo.
    echo How to get a token:
    echo   1. Go to: https://github.com/settings/tokens
    echo   2. Click 'Generate new token (classic)'
    echo   3. Name: 'FindBetter Updates'
    echo   4. Select scope: 'repo'
    echo   5. Click 'Generate token'
    echo   6. Copy the token
    echo.
    set /p GITHUB_TOKEN="Paste your GitHub token: "
    
    REM Download the update script using the token
    python -c "import urllib.request; req = urllib.request.Request('https://raw.githubusercontent.com/moranlevy420/birmanet/main/scripts/download_update.py', headers={'Authorization': 'token %GITHUB_TOKEN%'}); open('scripts/download_update.py', 'wb').write(urllib.request.urlopen(req).read())"
    
    if errorlevel 1 (
        echo [ERROR] Failed to download update script.
        echo Check your token and try again.
        pause
        exit /b 1
    )
    
    REM Save token for future use
    echo %GITHUB_TOKEN%> .github_token
    echo [OK] Token saved
)

REM Run the Python update script
python scripts/download_update.py

if errorlevel 1 (
    echo.
    echo [!] Update failed. Check errors above.
    pause
    exit /b 1
)

REM Install dependencies
echo.
echo Installing dependencies...
python -m pip install -r requirements.txt --quiet
echo [OK] Dependencies installed

REM Run database migrations
echo.
echo Running database migrations...
python scripts/run_migrations.py

REM Create/reset admin users
echo.
echo ========================================
echo    Setting up admin accounts...
echo ========================================
echo.
python scripts/init_admins.py

echo.
echo ========================================
echo    UPDATE COMPLETE!
echo ========================================
echo.
echo    IMPORTANT: Save your password above!
echo.
echo    To start the app, run: run_app.bat
echo.
echo ========================================
echo.
pause
