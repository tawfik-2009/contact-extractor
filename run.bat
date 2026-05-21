@echo off
chcp 65001 >nul
title Contact-AI | أداة استخراج بيانات العملاء

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║      🤖  Contact-AI - أداة استخراج العملاء      ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM ── Check Python ──────────────────────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [خطأ] Python غير مثبت على الجهاز.
    echo  يرجى تنزيله من: https://python.org/downloads
    echo  ثم تأكد من تفعيل خيار "Add to PATH" أثناء التثبيت.
    pause
    exit /b 1
)

echo  [1/4] جاري إعداد البيئة الافتراضية...
if not exist "venv" (
    python -m venv venv >nul 2>&1
    if %errorlevel% neq 0 (
        echo  [خطأ] فشل إنشاء البيئة الافتراضية.
        pause
        exit /b 1
    )
    echo        تم إنشاء البيئة بنجاح.
) else (
    echo        البيئة موجودة مسبقاً.
)

call venv\Scripts\activate.bat

echo  [2/4] جاري تثبيت المكتبات المطلوبة...
pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  [خطأ] فشل تثبيت المكتبات. تحقق من الاتصال بالإنترنت.
    pause
    exit /b 1
)
echo        تم تثبيت المكتبات بنجاح.

echo  [3/4] جاري تثبيت متصفح Chromium...
playwright install chromium --quiet 2>nul
echo        تم تجهيز المتصفح.

echo  [4/4] جاري تشغيل البرنامج...
echo.
echo  ══════════════════════════════════════════════════
echo   ✅ البرنامج يعمل الآن!
echo   افتح المتصفح على: http://localhost:5000
echo  ══════════════════════════════════════════════════
echo.

REM Open browser automatically after 2 seconds
start /b cmd /c "timeout /t 2 >nul && start http://localhost:5000"

python app.py

echo.
echo  [تم] تم إيقاف البرنامج.
pause
