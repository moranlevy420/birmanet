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

REM Create directories if they don't exist
if not exist "config" mkdir config
if not exist "models" mkdir models
if not exist "services" mkdir services
if not exist "ui" mkdir ui
if not exist "ui\components" mkdir ui\components
if not exist "ui\pages" mkdir ui\pages
if not exist "utils" mkdir utils

REM Download main files
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/app.py', 'app.py')"
echo [OK] app.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/requirements.txt', 'requirements.txt')"
echo [OK] requirements.txt

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/run_app.bat', 'run_app.bat')"
echo [OK] run_app.bat

REM Download config
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/config/settings.py', 'config/settings.py')"
echo [OK] config/settings.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/config/datasets.json', 'config/datasets.json')"
echo [OK] config/datasets.json

REM Download models
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/models/dataset.py', 'models/dataset.py')"
echo [OK] models/dataset.py

REM Download services
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/services/cache_service.py', 'services/cache_service.py')"
echo [OK] services/cache_service.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/services/data_service.py', 'services/data_service.py')"
echo [OK] services/data_service.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/services/update_service.py', 'services/update_service.py')"
echo [OK] services/update_service.py

REM Download UI
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/styles.py', 'ui/styles.py')"
echo [OK] ui/styles.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/components/charts.py', 'ui/components/charts.py')"
echo [OK] ui/components/charts.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/components/tables.py', 'ui/components/tables.py')"
echo [OK] ui/components/tables.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/components/sidebar.py', 'ui/components/sidebar.py')"
echo [OK] ui/components/sidebar.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/pages/world_view.py', 'ui/pages/world_view.py')"
echo [OK] ui/pages/world_view.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/pages/charts_page.py', 'ui/pages/charts_page.py')"
echo [OK] ui/pages/charts_page.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/pages/compare.py', 'ui/pages/compare.py')"
echo [OK] ui/pages/compare.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/pages/historical.py', 'ui/pages/historical.py')"
echo [OK] ui/pages/historical.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/pages/about.py', 'ui/pages/about.py')"
echo [OK] ui/pages/about.py

REM Download utils
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/utils/formatters.py', 'utils/formatters.py')"
echo [OK] utils/formatters.py

REM Create __init__.py files
echo. > config\__init__.py
echo. > models\__init__.py
echo. > services\__init__.py
echo. > ui\__init__.py
echo. > ui\components\__init__.py
echo. > ui\pages\__init__.py
echo. > utils\__init__.py

echo.
echo ========================================
echo    Update Complete!
echo ========================================
echo.
echo You can now run the app with run_app.bat
echo.
pause
