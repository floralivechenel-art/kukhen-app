import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Запрашиваем доступ ТОЛЬКО к файлам, созданным самим приложением (для безопасности)
SCOPES = ['https://www.googleapis.com/auth/drive.file']
BACKUP_FILE_NAME = "kukhen_backup.json"

def get_drive_service():
    """Авторизация и получение сервиса Google Drive"""
    creds = None
    # Файл token.json хранит ключи входа пользователя, чтобы не заставлять его логиниться каждый раз
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("Файл credentials.json не найден! Скачайте его из Google Cloud Console.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def upload_backup_to_drive(local_json_path="database.json"):
    """Загрузка локальной базы на Google Диск"""
    try:
        service = get_drive_service()
        
        # Ищем, есть ли уже старый бекап Kukhen на Диске
        results = service.files().list(
            q=f"name='{BACKUP_FILE_NAME}' and trashed=false",
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])

        media = MediaFileUpload(local_json_path, mimetype='application/json')

        if files:
            # Если файл есть — перезаписываем его (обновляем)
            file_id = files[0]['id']
            updated_file = service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            return True, "База рецептов успешно обновлена на Google Диске!"
        else:
            # Если файла нет — создаем новый
            file_metadata = {'name': BACKUP_FILE_NAME}
            created_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            return True, "База рецептов впервые сохранена на Google Диск!"

    except Exception as e:
        return False, f"Ошибка загрузки на Диск: {str(e)}"

def download_backup_from_drive(local_json_path="database.json"):
    """Скачивание базы с Google Диска и обновление локального файла"""
    try:
        service = get_drive_service()

        # Ищем файл бекапа на Диске
        results = service.files().list(
            q=f"name='{BACKUP_FILE_NAME}' and trashed=false",
            fields="files(id, name)"
        ).execute()
        files = results.get('files', [])

        if not files:
            return False, "На вашем Google Диске не найдено резервных копий Kukhen!"

        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)

        # Скачиваем и перезаписываем локальную базу
        with open(local_json_path, "wb") as f:
            f.write(request.execute())

        return True, "Рецепты успешно восстановлены с Google Диска!"

    except Exception as e:
        return False, f"Ошибка восстановления с Диска: {str(e)}"