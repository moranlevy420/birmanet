@echo off
title Pension Funds Explorer - Setup
color 0A

echo.
echo  ============================================
echo       PENSION FUNDS EXPLORER - SETUP
echo  ============================================
echo.
echo  This will install everything you need.
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  Python is not installed. Installing automatically...
    echo.
    
    :: Download Python installer
    echo  Downloading Python installer...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python_installer.exe'"
    
    if not exist python_installer.exe (
        echo.
        echo  [ERROR] Failed to download Python.
        echo  Please check your internet connection.
        echo  Or download manually from: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    echo  Installing Python (this may take a minute)...
    echo.
    
    :: Install Python silently with PATH
    python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
    
    :: Wait for installation
    timeout /t 10 /nobreak >nul
    
    :: Delete installer
    del python_installer.exe >nul 2>&1
    
    echo  [OK] Python installed!
    echo.
    echo  Please CLOSE this window and run INSTALL_WINDOWS.bat again.
    echo  (This is needed to refresh the PATH)
    echo.
    pause
    exit /b 0
)

echo  [OK] Python is installed!
echo.

:: Upgrade pip first
echo  Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

:: Install dependencies
echo  ============================================
echo       INSTALLING DEPENDENCIES
echo  ============================================
echo.
echo  Please wait, this may take a few minutes...
echo.

python -m pip install -r requirements.txt

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

:: Verify streamlit is installed
python -m streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [WARNING] Streamlit not found, trying again...
    python -m pip install streamlit
)

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
