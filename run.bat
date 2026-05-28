@echo off
chcp 65001 >nul
title Contact Extractor

echo.
echo ================================================
echo   Contact Extractor - Muqawil / Google Maps
echo ================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed.
    echo Download from: https://python.org/downloads
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/4] Setting up virtual environment...
if not exist "venv" (
    python -m venv venv >nul 2>&1
    echo       Done.
) else (
    echo       Already exists.
)
call venv\Scripts\activate.bat

echo [2/4] Installing libraries...
pip install flask flask-session flask-cors playwright openpyxl waitress requests beautifulsoup4 --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install libraries. Check internet connection.
    pause
    exit /b 1
)
echo       Done.

echo [3/4] Installing Chromium browser...
playwright install chromium >nul 2>&1
echo       Done.

echo [4/4] Starting app...
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set RAW_IP=%%a
    goto :found
)
:found
set LOCAL_IP=%RAW_IP: =%

echo ================================================
echo   App is running!
echo   Computer : http://localhost:5000
echo   iPhone   : http://%LOCAL_IP%:5000
echo   Username : admin
echo   Password : admin123
echo ================================================
echo.
echo   [Keep this window open while using the app]
echo.

start /b cmd /c "timeout /t 2 >nul && start http://localhost:5000"

python app.py

echo.
echo App stopped.
pause
