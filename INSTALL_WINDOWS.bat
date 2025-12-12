@echo off
title Pension Funds Explorer - Setup
color 0A

echo.
echo  ============================================
echo       PENSION FUNDS EXPLORER - SETUP
echo  ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Python is not installed. Installing automatically...
    echo.
    
    :: Download Python installer
    echo  Downloading Python installer...
    echo  (this may take a minute)
    echo.
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
    echo  Waiting for installation to complete...
    timeout /t 15 /nobreak
    
    :: Delete installer
    del python_installer.exe >nul 2>&1
    
    echo.
    echo  [OK] Python installed!
    echo.
    echo  ============================================
    echo  IMPORTANT: Close this window and run 
    echo  INSTALL_WINDOWS.bat again!
    echo  ============================================
    echo.
    pause
    exit /b 0
)

echo  [OK] Python found: 
python --version
echo.

:: Upgrade pip first
echo  Upgrading pip...
python -m pip install --upgrade pip
echo.

:: Install dependencies
echo  ============================================
echo       INSTALLING DEPENDENCIES
echo  ============================================
echo.
echo  This may take 2-3 minutes...
echo.

python -m pip install streamlit pandas requests plotly matplotlib seaborn streamlit-aggrid

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Failed to install some packages.
    echo  Trying alternative method...
    echo.
    python -m pip install -r requirements.txt
)

echo.
echo  Verifying installation...
echo.

:: Verify streamlit is installed
python -c "import streamlit; print('Streamlit:', streamlit.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo  [ERROR] Streamlit not installed correctly!
    echo.
    pause
    exit /b 1
)

python -c "import pandas; print('Pandas:', pandas.__version__)" 2>nul
python -c "import plotly; print('Plotly:', plotly.__version__)" 2>nul

echo.
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
