[app]
title = Clicker Game
package.name = clickergame
package.domain = com.yourcompany
source.dir = .
source.include_exts = py,kv,json,png,jpg,gif
icon.filename = %(source.dir)s/icon.png
version = 1.0
requirements = python3, kivy==2.3.1, android
orientation = portrait
fullscreen = 0

# إعدادات NDK و SDK الصحيحة
android.ndk = 25b 
android.api = 32
android.sdk = 32

android.minapi = 21
android.archs = armeabi-v7a, arm64-v8a
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.presplash = %(source.dir)s/presplash.png
buildozer.warn_on_error = 1
log_level = 2
