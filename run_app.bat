@echo off
title Pension Funds Explorer
color 0B

echo.
echo  ============================================
echo       PENSION FUNDS EXPLORER
echo  ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python is not installed!
    echo.
    echo  Please run INSTALL_WINDOWS.bat first.
    echo.
    pause
    exit /b 1
)

:: Check if streamlit is installed
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Dependencies not installed!
    echo.
    echo  Trying to install now...
    echo.
    python -m pip install -r requirements.txt
    
    :: Check again
    python -c "import streamlit" >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo  [ERROR] Still not working. Please run INSTALL_WINDOWS.bat
        echo.
        pause
        exit /b 1
    )
)

echo  Starting the app...
echo.
echo  Opening browser in 3 seconds...
echo.
echo  To STOP the app: close this window
echo.
echo  ============================================
echo.

:: Open browser after short delay
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8501"

:: Run streamlit
python -m streamlit run pensia_app.py --server.headless true

pause
