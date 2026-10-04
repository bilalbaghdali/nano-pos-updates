# NANO POS Updates

قناة التحديث الرسمية لبرنامج **NANO POS**.

يقرأ برنامج الكمبيوتر الملف:
`nano-pos-update.json`

## دورة النشر

1. ارفع مثبت Windows الجديد إلى MediaFire.
2. ضع رقم الإصدار، المميزات، رابط MediaFire و SHA-256 في `nano-pos-update.json`.
3. اترك `published: false` أثناء التحضير والاختبار.
4. بعد التأكد من الملف غيّرها إلى `published: true`.
5. سيكتشف NANO POS الإصدار الجديد تلقائيًا ويعرض مميزات التحديث للمستخدم.

## روابط MediaFire

- `download.directUrl`: رابط مباشر للملف. عند توفره يقوم NANO POS بالتنزيل داخليًا، يتحقق من SHA-256 ثم يشغل المثبت.
- `download.pageUrl`: رابط صفحة MediaFire العادي. يستخدم كخيار احتياطي ويفتح في المتصفح.

## الأمان

يفضل دائمًا إدخال `download.sha256` للملف المنشور. إذا لم يطابق الملف القيمة الموجودة في manifest، يرفض NANO POS تشغيله.

اسم المنتج الداخلي يبقى ثابتًا: **NANO POS**. رقم الإصدار مستقل ويتغير مع كل تحديث.


## التحديثات الخفيفة Patch

ابتداءً من NANO POS v1.0.11 يدعم البرنامج تحديثات خفيفة للإصلاحات الصغيرة.

يحتوي ملف Patch على `payload/app.asar` فقط. لا يتم تعديل userData أو قاعدة بيانات المتجر أو الترخيص أو مجلد backups.

مثال داخل `nano-pos-update.json`:

```json
{
  "version": "1.0.12",
  "patches": [
    {
      "fromVersion": "1.0.11",
      "directUrl": "DIRECT_PATCH_URL",
      "pageUrl": "",
      "sha256": "PATCH_ZIP_SHA256",
      "appAsarSha256": "APP_ASAR_SHA256",
      "fileName": "NANO-POS-Patch-1.0.11-to-1.0.12.zip",
      "sizeBytes": 0
    }
  ],
  "download": {
    "directUrl": "FULL_INSTALLER_DIRECT_URL",
    "pageUrl": "FULL_INSTALLER_PAGE_URL",
    "sha256": "FULL_INSTALLER_SHA256",
    "fileName": "NANO-POS-Setup-1.0.12-x64.exe"
  }
}
```

إذا كان الإصدار المثبت مطابقًا لـ `fromVersion` يستخدم NANO POS الـPatch. إذا لم يكن متوافقًا، أو فشل تنزيل/فحص Patch، ينتقل تلقائيًا إلى المثبت الكامل.

قبل استبدال `resources/app.asar` ينشئ المحرك نسخة Rollback، ويتحقق من SHA-256 للـZIP ثم من SHA-256 لملف `app.asar` الداخلي.
