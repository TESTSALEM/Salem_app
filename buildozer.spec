[app]
title = Click Master
package.name = ClickMaster
package.domain = com.salem
package.identifier = clicker

source.dir = .
source.include_exts = py,kv,png,jpg,ttf,wav,mp3
version = 1.0.0
orientation = portrait
fullscreen = 0
window = 0

requirements = python3, kivy==2.3.0
android.permissions = INTERNET,VIBRATE
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a,armeabi-v7a

android.accept_sdk_license = True
android.gradle_dependencies = com.android.support:multidex:1.0.3

icon.filename = icon.png

# مهم جداً لدعم البناء على GitHub Actions
android.sdk = auto
android.ndk = 23.1.7779620
android.ndk_version = 23b

log_level = 2
