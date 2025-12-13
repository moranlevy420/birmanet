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

echo Downloading latest version from GitHub...
echo.

REM Download files using Python
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/pensia_app.py', 'pensia_app.py')"
if errorlevel 1 (
    echo [ERROR] Failed to download pensia_app.py
    pause
    exit /b 1
)
echo [OK] pensia_app.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/requirements.txt', 'requirements.txt')"
if errorlevel 1 (
    echo [ERROR] Failed to download requirements.txt
    pause
    exit /b 1
)
echo [OK] requirements.txt

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/run_app.bat', 'run_app.bat')"
if errorlevel 1 (
    echo [ERROR] Failed to download run_app.bat
    pause
    exit /b 1
)
echo [OK] run_app.bat

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/INSTALL_WINDOWS.bat', 'INSTALL_WINDOWS.bat')"
if errorlevel 1 (
    echo [ERROR] Failed to download INSTALL_WINDOWS.bat
    pause
    exit /b 1
)
echo [OK] INSTALL_WINDOWS.bat

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/UPDATE_WINDOWS.bat', 'UPDATE_WINDOWS.bat')"
echo [OK] UPDATE_WINDOWS.bat

echo.
echo ========================================
echo    Update Complete!
echo ========================================
echo.
echo You can now run the app with run_app.bat
echo.
pause

