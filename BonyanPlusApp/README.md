# تطبيق بنيان بلس - Bonyan Plus App

تطبيق موبايل لموقع [bonyanplus.com](https://bonyanplus.com) يعمل على Android و iOS.

---

## المتطلبات

- [Node.js](https://nodejs.org/) v18 أو أحدث
- [Git](https://git-scm.com/)
- حساب على [Expo](https://expo.dev) (مجاني)

---

## التشغيل المحلي (للاختبار)

```bash
# 1. تثبيت المكتبات
npm install

# 2. تشغيل التطبيق
npm start
```

بعدها افتح تطبيق **Expo Go** على موبايلك وامسح الـ QR Code.

---

## بناء التطبيق للنشر (APK / IPA)

### الخطوة 1: تثبيت EAS CLI
```bash
npm install -g eas-cli
eas login
```

### الخطوة 2: ربط المشروع بـ Expo
```bash
eas init
```

### الخطوة 3: بناء التطبيق

**لأندرويد (APK للتجربة):**
```bash
npm run build:android -- --profile preview
```

**لأندرويد (AAB للنشر على Google Play):**
```bash
npm run build:android -- --profile production
```

**لـ iOS:**
```bash
npm run build:ios -- --profile production
```

---

## إضافة الأيقونات والشعار

ضع الصور في مجلد `assets/`:

| الملف | الحجم | الوصف |
|-------|-------|-------|
| `icon.png` | 1024×1024 | أيقونة التطبيق |
| `splash.png` | 1284×2778 | شاشة البداية |
| `adaptive-icon.png` | 1024×1024 | أيقونة أندرويد |

---

## تغيير لون التطبيق

افتح `App.tsx` وعدل المتغير:
```ts
const BRAND_COLOR = '#0e4d8d'; // لون بنيان بلس
```

وفي `app.json`:
```json
"backgroundColor": "#0e4d8d"
```

---

## هيكل المشروع

```
BonyanPlusApp/
├── App.tsx          ← الكود الرئيسي للتطبيق
├── app.json         ← إعدادات Expo (الاسم، الأيقونة، ...)
├── eas.json         ← إعدادات البناء
├── package.json     ← المكتبات المستخدمة
└── assets/          ← صور الأيقونات
```
