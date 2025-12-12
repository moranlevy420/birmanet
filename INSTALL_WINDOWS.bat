@echo off
title Pension Funds Explorer - Setup
color 0A

echo.
echo  ============================================
echo       PENSION FUNDS EXPLORER - SETUP
echo  ============================================
echo.
echo  This will install everything you need.
echo  Please follow the instructions below.
echo.
pause

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ============================================
    echo       STEP 1: INSTALL PYTHON
    echo  ============================================
    echo.
    echo  Python is not installed on your computer.
    echo.
    echo  A download page will open in your browser.
    echo.
    echo  IMPORTANT:
    echo  ----------
    echo  When installing Python, make sure to check:
    echo.
    echo     [X] Add Python to PATH
    echo.
    echo  This checkbox is at the BOTTOM of the installer!
    echo.
    pause
    start https://www.python.org/downloads/
    echo.
    echo  After installing Python, please RESTART this setup.
    echo.
    pause
    exit /b 1
)

echo.
echo  [OK] Python is installed!
echo.

:: Install dependencies
echo  ============================================
echo       STEP 2: INSTALLING DEPENDENCIES
echo  ============================================
echo.
echo  Please wait, this may take a few minutes...
echo.

pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Failed to install dependencies.
    echo  Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo  [OK] Dependencies installed!
echo.

:: Done
echo  ============================================
echo       SETUP COMPLETE!
echo  ============================================
echo.
echo  To run the app, double-click:
echo.
echo      run_app.bat
echo.
echo  ============================================
echo.
pause

