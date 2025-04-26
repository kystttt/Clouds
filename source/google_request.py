from googleapiclient.errors import HttpError
from google_auth import oauth_to_drive
import sys
import time
from progress.bar import Bar


def create_folder(path):
    """
    Создает вложенные папки на гугл диске
    :param path: str - путь, например "folder1/folder2/folder3"
    """
    service = oauth_to_drive()
    parent_id = None
    folders = path.strip("/").split("/")

    for folder_name in folders:
        query = (f"name='{folder_name}' and mimeType="
                 f"'application/vnd.google-apps.folder' and trashed=false")
        if parent_id:
            query += f" and '{parent_id}' in parents"

        try:
            response = service.files().list(q=query, fields="files(id)",
                                            spaces="drive").execute()
            files = response.get("files", [])

            if files:
                parent_id = files[0]["id"]
            else:
                metadata = {
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent_id] if parent_id else []
                }
                folder = service.files().create(body=metadata,
                                                fields="id").execute()
                parent_id = folder.get("id")

        except HttpError as error:
            print(f"Error, folder creation failed: {error}")
            sys.exit()
        except Exception as e:
            print("Unexpected error:", e)
            sys.exit()

    return parent_id


def delete_backup_on_drive(backup_name):
    """
    Функция, которая удаляет бэкап с Google Диска.
    :param backup_name: str - название папки с резервным
    сохранением на диске
    Пример: testFolder_2025_04_11
    """
    service = oauth_to_drive()

    try:
        query = (f"name='{backup_name}' and mimeType="
                 f"'application/vnd.google-apps.folder' and trashed=false")
        response = service.files().list(q=query, spaces="drive",
                                        fields="files(id, name)").execute()
        files = response.get("files", [])

        if not files:
            print("Error: backup not found")
            sys.exit()

        folder_id = files[0]['id']

        def count_files_in_folder(folder_id):
            """Рекурсивный подсчет файлов в папке и её подпапках"""
            result = 0
            query = f"'{folder_id}' in parents and trashed=false"
            response = service.files().list(q=query, spaces="drive",
                                            fields="files(id, mimeType)").execute()
            items = response.get("files", [])

            for item in items:
                if item["mimeType"] == ("application/"
                                        "vnd.google-apps.folder"):
                    result += count_files_in_folder(item["id"])
                else:
                    result += 1
            return result

        counter = count_files_in_folder(folder_id)
        bar = Bar('Deleting', fill='█', max=counter)
        for _ in range(counter):
            bar.next()
            time.sleep(0.5)

        service.files().delete(fileId=folder_id).execute()
        bar.finish()

        time.sleep(1)

        try:
            confirm_response = service.files().get(fileId=folder_id,
                                                   fields="trashed").execute()
            if confirm_response.get("trashed", False):
                print("Backup deleted!")
                sys.exit(0)
            else:
                print("Error: backup wasn't deleted")
                sys.exit()
        except HttpError as e:
            if e.resp.status == 404:
                print("Backup deleted!")
                sys.exit(0)
            else:
                print(f"Error: {e}")
                sys.exit()

    except HttpError as error:
        print(f"Error: {error}")
        sys.exit()
    except Exception as e:
        print("Unexpected error:", e)
        sys.exit()


