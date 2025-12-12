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
pip show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Dependencies not installed!
    echo.
    echo  Please run INSTALL_WINDOWS.bat first.
    echo.
    pause
    exit /b 1
)

echo  Starting the app...
echo.
echo  A browser window will open automatically.
echo.
echo  To STOP the app: close this window
echo.
echo  ============================================
echo.

streamlit run pensia_app.py

pause
