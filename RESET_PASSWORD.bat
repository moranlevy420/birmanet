@echo off
echo ========================================
echo    Find Better - Password Reset
echo ========================================
echo.

REM Download latest init_admins.py
echo Downloading latest script...
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/moranlevy420/birmanet/main/scripts/init_admins.py', 'scripts/init_admins.py')"

echo.
echo Resetting passwords...
echo.
python scripts/init_admins.py

echo.
echo ========================================
echo    SAVE YOUR NEW PASSWORD ABOVE!
echo ========================================
echo.
pause

