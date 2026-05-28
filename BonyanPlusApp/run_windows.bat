@echo off
title بنيان بلس - تشغيل التطبيق
color 0B
echo.
echo  ====================================
echo    بنيان بلس - جاري التشغيل...
echo  ====================================
echo.

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo  خطأ: Node.js غير مثبت!
    echo  حمّله من: https://nodejs.org
    echo  ثم افتح الملف مرة أخرى
    pause
    exit
)

echo  جاري تثبيت المكتبات...
call npm install

echo.
echo  جاري تشغيل التطبيق...
echo  امسح الـ QR Code بتطبيق Expo Go على iPhone
echo.
call npm start
pause
