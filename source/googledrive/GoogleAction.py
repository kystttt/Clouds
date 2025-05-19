import os
import mimetypes
from datetime import datetime, timezone
from googleapiclient.http import MediaFileUpload
from .google_auth import oauth_to_drive
from progress.bar import Bar
from googleapiclient.http import MediaIoBaseDownload
import io
from error_decorator import retry_on_error
import time
import sys



class GoogleAction:
    def __init__(self):
        self.service = oauth_to_drive()


    def backup(self, local_path):
        """
        Метод, который создает резервное копирование на гугл
        диске
        :param local_path: str - путь на машине
        Например: "D:\testFolder"
        """
        date_str = datetime.now().strftime("%Y_%m_%d")
        folder_name = os.path.basename(local_path)
        backup_folder_name = f"{folder_name}_{date_str}"
        self.upload(local_path, backup_folder_name)
        print("Backup completed!")
        sys.exit(0)


    @retry_on_error()
    def upload(self, local_path, root_folder_name=None):
        """
        Метод, который выгружает файлы на гугл диск
        :param local_path: str - путь к файлу на машине
        Например: "D:\testFolder\testFile.txt
        """
        root_folder_name = root_folder_name or os.path.basename(local_path)
        parent_id = self._get_or_create_folder(root_folder_name, None)

        total_files = sum(len(files) for _, _, files in os.walk(local_path))
        bar = Bar("Uploading",  fill='█',max=total_files)

        for root, dirs, files in os.walk(local_path):
            relative_path = os.path.relpath(root, local_path)
            current_parent_id = parent_id

            if relative_path != ".":
                for part in relative_path.split(os.sep):
                    current_parent_id = self._get_or_create_folder(part, current_parent_id)

            for file in files:
                file_path = os.path.join(root, file)
                self._upload_file(file_path, current_parent_id)
                bar.next()

        bar.finish()

    @retry_on_error()
    def _get_or_create_folder(self, name, parent_id):
        """
        Получает ID существующей папки на Google Диске с
        заданным именем или создает новую, если такая не найдена.
        :param name: str - Название папки, которую нужно найти или
        создать
        :param parent_id: str - ID родительской папки
        :return:
        """
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = self.service.files().list(q=query, spaces='drive', fields="files(id)").execute()
        items = results.get('files', [])

        if items:
            return items[0]['id']

        metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id] if parent_id else []
        }
        folder = self.service.files().create(body=metadata, fields='id').execute()
        return folder['id']


    @retry_on_error()
    def _upload_file(self, file_path, parent_id):
        """
        Метод, который загружает файл на облако
        :param file_path: путь к файлу
        :param parent_id: парент айди
        """
        file_name = os.path.basename(file_path)
        query = f"name='{file_name}' and '{parent_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, spaces='drive', fields="files(id, modifiedTime)").execute()
        items = results.get('files', [])

        local_time = datetime.fromtimestamp(os.path.getmtime(file_path), timezone.utc)

        file_metadata = {'name': file_name, 'parents': [parent_id]}
        mimetype = mimetypes.guess_type(file_path)[0]
        media = MediaFileUpload(file_path, mimetype=mimetype, resumable=True)

        if items:
            drive_time = datetime.fromisoformat(items[0]['modifiedTime'].replace("Z", "+00:00"))
            if local_time <= drive_time:
                return
            request = self.service.files().update(fileId=items[0]['id'], media_body=media)
        else:
            request = self.service.files().create(body=file_metadata, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()


    @retry_on_error()
    def download(self, backup_name, path_on_machine):
        """
        Скачивает бэкап с Google Диска
        :param path_on_machine: локальный путь на ПК, куда скачивать
        :param backup_name: имя папки бэкапа на Google Диске
        """

        def get_folder_id_by_name(name, parent_id=None):
            query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            results = self.service.files().list(q=query, spaces='drive', fields="files(id)").execute()
            items = results.get("files", [])
            if not items:
                raise FileNotFoundError(f"Folder '{name}' not found in Google Drive.")
            return items[0]["id"]


        def list_folder_contents(folder_id):
            files = []
            page_token = None
            while True:
                response = self.service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                    pageToken=page_token
                ).execute()
                files.extend(response.get("files", []))
                page_token = response.get("nextPageToken", None)
                if page_token is None:
                    break
            return files


        def count_files(folder_id):
            """Рекурсивно подсчитывает количество файлов"""
            count = 0
            for item in list_folder_contents(folder_id):
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    count += count_files(item['id'])
                else:
                    count += 1
            return count


        def download_recursive(folder_id, current_local_path):
            os.makedirs(current_local_path, exist_ok=True)
            for item in list_folder_contents(folder_id):
                item_name = item['name']
                item_path = os.path.join(current_local_path, item_name)

                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    download_recursive(item['id'], item_path)
                else:
                    drive_time = datetime.fromisoformat(item['modifiedTime'].replace("Z", "+00:00"))
                    if os.path.exists(item_path):
                        local_time = datetime.fromtimestamp(os.path.getmtime(item_path), timezone.utc)
                        if local_time >= drive_time:
                            bar.next()
                            continue

                    request = self.service.files().get_media(fileId=item['id'])
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request, chunksize=1024 * 1024)  # 1 MB
                    done = False

                    while not done:
                        status, done = downloader.next_chunk()

                    with open(item_path, 'wb') as f:
                        f.write(fh.getbuffer())

                    os.utime(item_path, (int(drive_time.timestamp()), int(drive_time.timestamp())))
                    bar.next()

        backup_folder_id = get_folder_id_by_name(backup_name)
        total_files = count_files(backup_folder_id)
        bar = Bar("Downloading", fill='█', max=total_files)
        target_path = os.path.join(path_on_machine, backup_name)
        download_recursive(backup_folder_id, target_path)
        bar.finish()
        print("Download completed!")
        sys.exit(0)

    @retry_on_error()
    def delete_backup_on_cloud(self, backup_name):
        """
        Удаляет бэкап (папку с файлами) с Google Диска по названию.
        :param backup_name: str — Название папки, например 'testFolder_2025_04_11'
        """
        folder_id = self._get_folder_id_by_name(backup_name)
        if not folder_id:
            print("Error: backup not found")
            sys.exit(1)
        files = self._list_all_files_recursive(folder_id)
        bar = Bar("Deleting", fill='█', max=len(files))
        for file in files:
            self.service.files().delete(fileId=file['id']).execute()
            time.sleep(0.1)
            bar.next()
        self.service.files().delete(fileId=folder_id).execute()
        bar.finish()
        time.sleep(1)
        confirm = self._get_folder_id_by_name(backup_name)
        if not confirm:
            print("Backup deleted!")
            sys.exit(0)
        else:
            print("Error: backup wasn't deleted")
            sys.exit(1)


    @retry_on_error()
    def _get_folder_id_by_name(self, name, parent_id=None):
        """
        Находит айди папки по ее имени
        :param name: str - имя папки
        :param parent_id: айди родителя (папки, для которой данная
        директория является вложенной)
        """
        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        results = self.service.files().list(q=query, spaces='drive', fields="files(id)").execute()
        items = results.get("files", [])
        return items[0]["id"] if items else None


    @retry_on_error()
    def list_of_files_on_backup(self, backup_name):
        """
        Выводит структуру файлов и папок в бэкапе на гугл диске
        :param backup_name: Str - Название папки-бэкапа на гугл
        диске
        """
        folder_id = self._get_folder_id_by_name(backup_name)
        if not folder_id:
            print(f"Error: Backup folder '{backup_name}' not found.")
            return
        print(f"{backup_name}: ")
        def print_recursive(folder_id, indent=""):
            items = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="files(id, name, mimeType)"
            ).execute().get("files", [])

            for item in items:
                print(f"{indent} {item['name']}:")
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    print_recursive(item['id'], indent + "  ")
        print_recursive(folder_id)


    @retry_on_error()
    def _list_all_files_recursive(self, folder_id):
        """Рекурсивно получает список всех файлов и папок внутри
        папки"""
        all_items = []

        def traverse(folder_id):
            page_token = None
            while True:
                response = self.service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    fields="nextPageToken, files(id, name, mimeType)",
                    pageToken=page_token
                ).execute()
                items = response.get("files", [])
                for item in items:
                    if item['mimeType'] == 'application/vnd.google-apps.folder':
                        traverse(item['id'])
                    all_items.append(item)
                page_token = response.get("nextPageToken")
                if not page_token:
                    break

        traverse(folder_id)
        return all_items
