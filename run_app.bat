@echo off
echo Starting Find Better...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please run INSTALL_WINDOWS.bat first.
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Dependencies not installed!
    echo Please run INSTALL_WINDOWS.bat first.
    pause
    exit /b 1
)

REM Open browser after a delay
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8501"

REM Run the app
python -m streamlit run app.py --server.headless true

pause
