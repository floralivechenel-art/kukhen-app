import os
import json
import tempfile
import sys
import importlib

# ANDROID FIX: Настраиваем каталог кэша ПЕРЕД импортом googleapiclient
# Это предотвращает попытку доступа к файлам внутри sitepackages.zip
try:
    # На Android используем временный каталог приложения
    if hasattr(sys, 'mobile') or 'FLET_ANDROID' in os.environ or os.path.exists('/data/data'):
        # Создаем каталог кэша в доступной директории
        cache_dir = os.path.expanduser('~/.cache/kukhen')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        os.environ['GOOGLE_API_PYTHON_CLIENT_CACHE_DIR'] = cache_dir
except Exception:
    pass

# Отключаем файловый кэш googleapiclient на уровне переменных окружения
os.environ['GOOGLE_PYTHON_CLIENT_PREVENT_FILE_CACHE'] = '1'

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Запрашиваем доступ ТОЛЬКО к файлам, созданным самим приложением
SCOPES = ['https://www.googleapis.com/auth/drive.file']
BACKUP_FILE_NAME = "kukhen_backup.json"

# Вычисляем точный путь к директории приложения на устройстве
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')

def get_drive_service():
    """Авторизация и получение сервиса Google Drive по токену"""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Сохраняем обновленный токен обратно в файл
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
        else:
            raise FileNotFoundError(
                "Файл token.json не найден или недействителен!"
            )

    # ANDROID FIX: Отключаем ВСЕ виды кэширования для правильной работы на мобильных устройствах
    try:
        return build(
            'drive', 'v3', 
            credentials=creds, 
            cache_discovery=False,
            static_discovery=False  # Предотвращает загрузку статических файлов
        )
    except Exception as e:
        # Если произойдет ошибка с кэшем, пробуем еще раз с более жесткими ограничениями
        try:
            # Очищаем кэш модулей googleapiclient
            if 'googleapiclient.discovery' in sys.modules:
                importlib.reload(sys.modules['googleapiclient.discovery'])
        except:
            pass
        
        return build(
            'drive', 'v3', 
            credentials=creds, 
            cache_discovery=False,
            static_discovery=False
        )

def upload_backup_to_drive(local_json_path=None):
    """Загрузка локальной базы на Google Диск"""
    if local_json_path is None:
        local_json_path = os.path.join(BASE_DIR, "database.json")

    try:
        if not os.path.exists(local_json_path):
            return False, "Локальный файл базы данных рецептов не найден!"

        service = get_drive_service()
        
        # Поиск предыдущего бэкапа
        results = service.files().list(
            q=f"name='{BACKUP_FILE_NAME}' and trashed=false",
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])

        media = MediaFileUpload(local_json_path, mimetype='application/json')

        if files:
            # Обновляем существующий файл бэкапа
            file_id = files[0]['id']
            service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            return True, "База рецептов успешно обновлена на Google Диске!"
        else:
            # Создаем новый файл бэкапа
            file_metadata = {'name': BACKUP_FILE_NAME}
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            return True, "База рецептов впервые сохранена на Google Диск!"

    except IsADirectoryError as e:
        # ANDROID FIX: Обработка ошибки с доступом к ZIP-архиву как к директории
        return False, "Ошибка доступа к файловой системе (проблема с кэшем). Пожалуйста, перезагрузите приложение и попробуйте снова."
    except PermissionError as e:
        # Обработка ошибок доступа на Android
        return False, "Нет разрешения на доступ к файлам. Пожалуйста, проверьте разрешения приложения."
    except Exception as e:
        error_msg = str(e)
        # Скрываем внутренние пути для лучшей читаемости ошибки
        if 'sitepackages.zip' in error_msg:
            return False, "Ошибка кэша библиотеки. Пожалуйста, очистите данные приложения и попробуйте снова."
        return False, f"Ошибка загрузки на Диск: {error_msg}"

def download_backup_from_drive(local_json_path=None):
    """Скачивание базы с Google Диска и обновление локального файла"""
    if local_json_path is None:
        local_json_path = os.path.join(BASE_DIR, "database.json")

    try:
        service = get_drive_service()

        results = service.files().list(
            q=f"name='{BACKUP_FILE_NAME}' and trashed=false",
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])

        if not files:
            return False, "На вашем Google Диске не найдено резервных копий Kukhen!"

        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)

        with open(local_json_path, "wb") as f:
            f.write(request.execute())

        return True, "Рецепты успешно восстановлены с Google Диска!"

    except IsADirectoryError as e:
        # ANDROID FIX: Обработка ошибки с доступом к ZIP-архиву как к директории
        return False, "Ошибка доступа к файловой системе (проблема с кэшем). Пожалуйста, перезагрузите приложение и попробуйте снова."
    except PermissionError as e:
        # Обработка ошибок доступа на Android
        return False, "Нет разрешения на доступ к файлам. Пожалуйста, проверьте разрешения приложения."
    except Exception as e:
        error_msg = str(e)
        # Скрываем внутренние пути для лучшей читаемости ошибки
        if 'sitepackages.zip' in error_msg:
            return False, "Ошибка кэша библиотеки. Пожалуйста, очистите данные приложения и попробуйте снова."
        return False, f"Ошибка восстановления с Диска: {error_msg}"

def check_sync_status():
    """Проверяет статус синхронизации (для логирования и отладки)"""
    try:
        # Проверяем наличие токена
        if not os.path.exists(TOKEN_PATH):
            return False, "Токен Google авторизации не найден. Пожалуйста, авторизуйтесь."
        
        # Пытаемся получить сервис
        service = get_drive_service()
        
        # Проверяем доступ к Google Drive
        about = service.about().get(fields='user').execute()
        
        return True, f"Синхронизация работает. Аккаунт: {about['user']['displayName']}"
    
    except FileNotFoundError as e:
        return False, "Ошибка авторизации. Пожалуйста, авторизуйтесь заново."
    except Exception as e:
        error_msg = str(e)
        if 'No internet' in error_msg or 'ConnectionError' in error_msg:
            return False, "Нет интернет-соединения. Данные сохранены локально."
        return False, f"Ошибка проверки синхронизации: {error_msg}"