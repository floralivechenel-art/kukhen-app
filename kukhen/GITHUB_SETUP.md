# 📤 Загрузка проекта на GitHub

## Шаг 1: Создать репозиторий на GitHub

1. Откройте https://github.com/new
2. Заполните:
   - **Repository name**: `kukhen`
   - **Description**: `Мобильное приложение для управления рецептами с синхронизацией Google Drive`
   - **Public/Private**: Выберите нужное
3. Нажмите **Create repository**

## Шаг 2: Инициализировать Git локально

```bash
cd c:\VSCode\kukhen

# Инициализировать репозиторий
git init

# Добавить все файлы
git add .

# Создать первый коммит
git commit -m "Initial commit: Kukhen app with Google Drive sync"

# Добавить ссылку на GitHub
# Замените USERNAME и REPO_NAME
git remote add origin https://github.com/USERNAME/kukhen.git

# Отправить на GitHub
git branch -M main
git push -u origin main
```

## Шаг 3: Проверить GitHub Actions

1. Откройте https://github.com/USERNAME/kukhen
2. Перейдите на вкладку **Actions**
3. Вы должны увидеть запущенный workflow "Build APK for Android"
4. Дождитесь завершения (5-15 минут)
5. Если всё успешно, вы увидите зелёную галочку ✅

## Шаг 4: Скачать готовый APK

1. В GitHub откройте последний успешный workflow
2. Нажмите **Artifacts** (внизу страницы)
3. Скачайте `kukhen-debug-apk.zip`
4. Распакуйте и установите на телефон:
   ```bash
   adb install kukhen-1.0-debug.apk
   ```

## 🚀 Дальше

После каждого `git push origin main`:
- ✅ GitHub Actions автоматически соберет новый APK
- ✅ Вы сможете скачать его из Artifacts
- ✅ Установить на телефон и протестировать

## 💡 Советы

### Если сборка не удалась
1. Откройте workflow в Actions
2. Посмотрите лог ошибки
3. Исправьте проблему локально
4. Сделайте `git push` и попробуйте снова

### Команды для работы с Git

```bash
# Просмотр статуса
git status

# Добавить файлы
git add .

# Создать коммит
git commit -m "Описание изменений"

# Отправить на GitHub
git push origin main

# Скачать обновления с GitHub
git pull origin main

# Просмотр истории
git log --oneline
```

### Если забыли установить Git

На Windows:
```powershell
# Установить Git
choco install git

# ИЛИ скачать отсюда: https://git-scm.com/download/win
```

---

**Готово!** Теперь ваше приложение будет автоматически собираться на облаке при каждом push! 🎉
