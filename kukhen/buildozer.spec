[app]

title = Kukhen
package.name = kukhen
package.domain = org.kukhen

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0

requirements = python3,kivy,flet,google-auth,google-api-python-client,google-auth-oauthlib,google-auth-httplib2,requests

# РАЗРЕШЕНИЯ НА ANDROID
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Версии Android SDK
android.api = 31
android.minapi = 21
android.ndk = 25b
android.build_tools_version = 37.0.0

# Архитектуры
android.archs = arm64-v8a

# Опции сборки
android.gradle_dependencies = 
android.add_src = 

# Логирование
log_level = 2
warn_on_root = 1
