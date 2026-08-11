[app]

title = Kukhen
package.name = kukhen
package.domain = org.kukhen

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0

requirements = python3,kivy,flet,google-auth,google-api-python-client,google-auth-oauthlib,google-auth-httplib2,requests

# РАЗРЕШЕНИЯ НА ANDROID
# Позволяет приложению читать и писать на внутреннее хранилище
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Уровень API для Android
android.api = 31
android.minapi = 21

# Архитектуры
android.archs = arm64-v8a,armeabi-v7a

# Ориентация экрана
orientation = portrait

# Иконка и оформление
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

# Логирование
log_level = 2
warn_on_root = 1
