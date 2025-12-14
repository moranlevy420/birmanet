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
if not exist "migrations" mkdir migrations
if not exist "migrations\versions" mkdir migrations\versions
if not exist "scripts" mkdir scripts

REM Download main files
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/app.py', 'app.py')"
echo [OK] app.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/manage.py', 'manage.py')"
echo [OK] manage.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/alembic.ini', 'alembic.ini')"
echo [OK] alembic.ini

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/requirements.txt', 'requirements.txt')"
echo [OK] requirements.txt

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/run_app.bat', 'run_app.bat')"
echo [OK] run_app.bat

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/INSTALL_WINDOWS.bat', 'INSTALL_WINDOWS.bat')"
echo [OK] INSTALL_WINDOWS.bat

REM Download config
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/config/__init__.py', 'config/__init__.py')"
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/config/settings.py', 'config/settings.py')"
echo [OK] config/settings.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/config/datasets.json', 'config/datasets.json')"
echo [OK] config/datasets.json

REM Download models
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/models/__init__.py', 'models/__init__.py')"
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/models/dataset.py', 'models/dataset.py')"
echo [OK] models/dataset.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/models/database.py', 'models/database.py')"
echo [OK] models/database.py

REM Download services
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/services/__init__.py', 'services/__init__.py')"
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/services/cache_service.py', 'services/cache_service.py')"
echo [OK] services/cache_service.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/services/data_service.py', 'services/data_service.py')"
echo [OK] services/data_service.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/services/update_service.py', 'services/update_service.py')"
echo [OK] services/update_service.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/services/db_service.py', 'services/db_service.py')"
echo [OK] services/db_service.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/services/auth_service.py', 'services/auth_service.py')"
echo [OK] services/auth_service.py

REM Download UI
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/__init__.py', 'ui/__init__.py')"
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/styles.py', 'ui/styles.py')"
echo [OK] ui/styles.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/components/__init__.py', 'ui/components/__init__.py')"
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/components/charts.py', 'ui/components/charts.py')"
echo [OK] ui/components/charts.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/components/tables.py', 'ui/components/tables.py')"
echo [OK] ui/components/tables.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/components/sidebar.py', 'ui/components/sidebar.py')"
echo [OK] ui/components/sidebar.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/components/auth.py', 'ui/components/auth.py')"
echo [OK] ui/components/auth.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/pages/__init__.py', 'ui/pages/__init__.py')"
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

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/pages/settings.py', 'ui/pages/settings.py')"
echo [OK] ui/pages/settings.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/ui/pages/find_better.py', 'ui/pages/find_better.py')"
echo [OK] ui/pages/find_better.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/services/find_better_service.py', 'services/find_better_service.py')"
echo [OK] services/find_better_service.py

REM Download utils
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/utils/__init__.py', 'utils/__init__.py')"
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/utils/formatters.py', 'utils/formatters.py')"
echo [OK] utils/formatters.py

REM Download migrations
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/migrations/env.py', 'migrations/env.py')"
echo [OK] migrations/env.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/migrations/script.py.mako', 'migrations/script.py.mako')"
echo [OK] migrations/script.py.mako

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/migrations/versions/20241213_0001_initial_schema.py', 'migrations/versions/20241213_0001_initial_schema.py')"
echo [OK] migrations/versions/initial_schema.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/migrations/versions/20241214_0002_add_system_settings.py', 'migrations/versions/20241214_0002_add_system_settings.py')"
echo [OK] migrations/versions/system_settings.py

REM Download scripts
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/scripts/init_admins.py', 'scripts/init_admins.py')"
echo [OK] scripts/init_admins.py

python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/scripts/run_migrations.py', 'scripts/run_migrations.py')"
echo [OK] scripts/run_migrations.py

REM Install all dependencies from requirements.txt
echo.
echo Installing dependencies...
python -m pip install -r requirements.txt --quiet
echo [OK] Dependencies installed

REM Run database migrations (preserves existing data!)
echo.
echo Running database migrations...
python scripts/run_migrations.py
echo [OK] Database migrated

REM Create/reset admin users and show passwords
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
