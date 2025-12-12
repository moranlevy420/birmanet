@echo off
title Pension Funds Explorer - Uninstall
color 0C

echo.
echo  ============================================
echo       PENSION FUNDS EXPLORER - UNINSTALL
echo  ============================================
echo.
echo  This will remove the app dependencies.
echo.
echo  Note: Python itself will NOT be removed
echo  (you may need it for other apps)
echo.
pause

:: Remove installed packages
echo.
echo  Removing dependencies...
echo.

python -m pip uninstall streamlit streamlit-aggrid plotly pandas requests matplotlib seaborn -y >nul 2>&1

echo  [OK] Dependencies removed!
echo.

:: Ask about cache
if exist pension_cache.db (
    echo  Removing cache file...
    del pension_cache.db >nul 2>&1
    echo  [OK] Cache removed!
    echo.
)

if exist column_state.json (
    del column_state.json >nul 2>&1
)

:: Done
echo  ============================================
echo       UNINSTALL COMPLETE!
echo  ============================================
echo.
echo  To fully remove the app:
echo  Just delete this folder.
echo.
echo  ============================================
echo.
pause

