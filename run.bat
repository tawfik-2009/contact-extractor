@echo off
chcp 65001 >nul
title مستخرج جهات التواصل - شركات مقاولات

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║    🏗️   مستخرج جهات التواصل - شركات مقاولات       ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

REM ── Check Python ──────────────────────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [خطأ] Python غير مثبت.
    echo  حمّله من: https://python.org/downloads
    echo  ثم فعّل "Add Python to PATH" عند التثبيت.
    pause
    exit /b 1
)

REM ── Virtual environment ───────────────────────────────────────────────────
echo  [1/4] جاري إعداد البيئة...
if not exist "venv" (
    python -m venv venv >nul 2>&1
    echo        تم إنشاء البيئة.
) else (
    echo        البيئة موجودة.
)
call venv\Scripts\activate.bat

REM ── Install requirements ──────────────────────────────────────────────────
echo  [2/4] جاري تثبيت المكتبات...
pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  [خطأ] فشل تثبيت المكتبات. تحقق من الإنترنت.
    pause
    exit /b 1
)
echo        تم تثبيت المكتبات.

REM ── Playwright Chromium ───────────────────────────────────────────────────
echo  [3/4] جاري تجهيز متصفح Chromium...
playwright install chromium >nul 2>&1
echo        تم تجهيز المتصفح.

REM ── Get local IP ─────────────────────────────────────────────────────────
echo  [4/4] جاري تشغيل التطبيق...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP: =%

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║   ✅ التطبيق يعمل الآن!                             ║
echo  ╠══════════════════════════════════════════════════════╣
echo  ║   💻 على الكمبيوتر : http://localhost:5000          ║
echo  ║   📱 على الآيفون   : http://%LOCAL_IP%:5000    ║
echo  ╠══════════════════════════════════════════════════════╣
echo  ║   يوزر: admin   ^|   باسورد: admin123               ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  [اضغط Ctrl+C لإيقاف التطبيق]
echo.

REM Open browser automatically
start /b cmd /c "timeout /t 2 >nul && start http://localhost:5000"

python app.py

echo.
echo  [تم] تم إيقاف التطبيق.
pause
