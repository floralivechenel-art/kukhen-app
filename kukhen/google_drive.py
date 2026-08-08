import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Запрашиваем доступ ТОЛЬКО к файлам, созданным самым приложением
SCOPES = ['https://www.googleapis.com/auth/drive.file']
BACKUP_FILE_NAME = "kukhen_backup.json"

# Вычисляем точный путь к директории приложения на устройстве
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')

def get_drive_service():
    """Авторизация и получение сервиса Google Drive"""
    creds = None

    # Проверяем наличие токена авторизации
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError("Файл credentials.json не найден! Поместите его рядом с main.py.")
            
            # Для мобильных устройств используем порт 8080 или редирект на urn:ietf:wg:oauth:2.0:oob
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            
            # В зависимости от типа клиента в Google Cloud Console:
            try:
                # Пробуем запустить с закрытием порта для мобильных WebView
                creds = flow.run_local_server(port=8080, open_browser=True)
            except Exception:
                # Если локальный сервер недоступен на Android, используется прямой поток
                flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                auth_url, _ = flow.authorization_url(prompt='consent')
                raise RuntimeError(f"Перейдите по ссылке для авторизации: {auth_url}")
            
        # Сохраняем сессию
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

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

    except Exception as e:
        return False, f"Ошибка загрузки на Диск: {str(e)}"

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

    except Exception as e:
        return False, f"Ошибка восстановления с Диска: {str(e)}"