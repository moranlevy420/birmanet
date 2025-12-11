@echo off
echo ========================================
echo   Pension Funds Explorer - Starting...
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

:: Check if requirements are installed
echo Checking dependencies...
pip show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting the app...
echo The browser will open automatically.
echo To stop the app, close this window or press Ctrl+C
echo.

:: Run Streamlit
streamlit run pensia_app.py

pause

