# 📱 Kukhen — Личные рецепты

Мобильное приложение для управления рецептами на Android с автоматической синхронизацией на Google Drive.

## ✨ Возможности

- 📝 Добавление, редактирование и удаление рецептов
- 🛒 Создание списка покупок на основе выбранных рецептов
- 📊 Агрегирование ингредиентов по категориям
- ☁️ Автоматическая синхронизация с Google Drive
- 💾 Локальное сохранение данных на телефон
- 🔄 Восстановление данных с облака одной кнопкой

## 🚀 Быстрый старт

### На ПК (для тестирования)
```bash
pip install -r requirements.txt
flet run
```

### На Android
Приложение автоматически собирается GitHub Actions при каждом push.

1. Откройте GitHub репозиторий
2. Перейдите в **Actions** → **Build APK for Android**
3. Скачайте APK из последней успешной сборки
4. Установите на телефон

## 📋 Требования

- Python 3.11+
- Flet для UI
- Google API Python Client для синхронизации
- Android 5.1+ для мобильного приложения

## 📦 Зависимости

```
flet>=0.21.0
google-auth>=2.25.0
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
requests>=2.31.0
```

## 🔐 Синхронизация с Google Drive

### Первая авторизация
1. При первом использовании приложение запросит доступ к Google Drive
2. Откроется браузер для авторизации в Google
3. Разрешите доступ к приложению
4. Токен сохранится в файл `token.json`

### Как это работает
- **Локально**: Все рецепты сохраняются в `database.json` на телефоне
- **В облаке**: Автоматически отправляются на Google Drive как `kukhen_backup.json`
- **Восстановление**: Кнопка ☁️ скачивает последнюю версию с облака

## 📁 Структура проекта

```
kukhen/
├── main.py                 # Главное приложение Flet
├── google_drive.py         # Логика синхронизации с Google Drive
├── requirements.txt        # Зависимости Python
├── buildozer.spec          # Конфигурация сборки Android
├── core/
│   ├── models.py          # Модели данных (Recipe, Ingredient)
│   ├── aggregator.py      # Агрегирование ингредиентов
│   └── __init__.py
├── storage/
│   ├── repository.py      # Работа с БД (JSON)
│   └── __init__.py
├── .github/
│   └── workflows/
│       └── build.yml      # GitHub Actions для сборки APK
└── README.md              # Этот файл
```

## 🛠️ Разработка

### Локальное тестирование
```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить приложение
flet run
```

### Сборка APK

#### Способ 1: GitHub Actions (рекомендуется)
```bash
git push origin main
# GitHub автоматически соберет APK
# Скачайте из Actions → Artifacts
```

#### Способ 2: Локально (требует Buildozer)
```bash
pip install buildozer cython
cd kukhen
buildozer android debug
# APK будет в bin/kukhen-1.0-debug.apk
```

## 🐛 Решение проблем

### Ошибка "sitepackages.zip" на Android
**Решение**: Эта ошибка уже исправлена в коде. Используется отдельный каталог кэша.

### Разрешения не запрашиваются
**Решение**: 
1. Перезагрузите приложение
2. Откройте Параметры → Приложения → Kukhen → Разрешения
3. Включите INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

### Синхронизация не работает
1. Проверьте интернет-соединение
2. Убедитесь, что разрешения включены
3. Удалите `token.json` и авторизуйтесь заново
4. Попробуйте кнопку ☁️ для восстановления

## 📚 Дополнительная информация

- [SYNC_GUIDE.md](SYNC_GUIDE.md) — Полная документация по синхронизации
- [BUILD_ANDROID.md](BUILD_ANDROID.md) — Инструкция по сборке
- [QUICK_START.md](QUICK_START.md) — Краткий старт

## 📄 Лицензия

Проект создан с использованием:
- [Flet](https://flet.dev) — фреймворк UI
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)

## 👨‍💻 Разработка

Репозиторий содержит:
- Автоматическую сборку APK через GitHub Actions
- Конфигурацию для всех необходимых разрешений Android
- Синхронизацию с Google Drive
- Примеры использования Flet

---

**Готово к использованию!** 🚀
