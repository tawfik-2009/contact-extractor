#!/bin/bash
echo ""
echo "===================================="
echo "  بنيان بلس - جاري التشغيل..."
echo "===================================="
echo ""

if ! command -v node &> /dev/null; then
    echo "خطأ: Node.js غير مثبت!"
    echo "حمّله من: https://nodejs.org"
    exit 1
fi

echo "جاري تثبيت المكتبات..."
npm install

echo ""
echo "جاري تشغيل التطبيق..."
echo "امسح الـ QR Code بتطبيق Expo Go على iPhone"
echo ""
npm start
