[app]
# (الإعدادات الأساسية)
title = Click Master
package.name = clickmaster
package.domain = com.salem
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json,ttf,otf,mp3,wav
version = 0.1
# إذا أردت زيادة رقم النسخة قبل رفع كل تحديث غيّر version
# (يمكن استخدام version.code = 1 لرقم داخلي)
version.code = 1
orientation = portrait
# المتطلبات: عدّل إصدارات الحزم إن لزم
requirements = python3,kivy==2.1.0
# السماح بالإنترنت (إذا تحتاجه)
android.permissions = INTERNET

# ملف kv الرئيسي
# (تأكد أن اسم الملف في الكود يطابق: game_design.kv)
# (Buildozer سيضم كل الملفات المذكورة في source.include_exts)

# العرض والرموز (غير إلزامي هنا)
icon.filename = %(source.dir)s/icon.png

# إعدادات Android (حدّث api / build-tools حسب الحاجة)
android.api = 33
android.minapi = 21
android.sdk = 24
android.ndk = 25b
android.build_tools_version = 33.0.2

# قبول تراخيص SDK تلقائياً (تفعيل من قبل workflow أيضاً)
android.accept_sdk_license = True

# إعداد توقيع الإصدار (ضع مسارات/أسماء ولكن سننزل keystore من السكربت)
# تُملأ عند التوقيع داخل CI عبر GitHub secrets
# android.release_keystore = /home/user/.android/mykey.keystore
# android.keystore_password = your_keystore_password
# android.keyalias = mykeyalias
# android.keyalias_password = your_key_alias_password

# استخدام gradle (buildozer يستخدم now gradle backend)
android.use_gradle = True

# الحدّ الأقصى لحجم الحزمة
# (يمكن تعديل أو إزالة)
android.max_binary_size = 100

# Packaging: يمكنك طلب AAB بدل APK عبر الأمر buildozer android release aab
# لكن Buildozer غالبًا ينتج APK; سنحاول إنتاج AAB إن أمكن عبر gradle
