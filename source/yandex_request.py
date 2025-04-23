import sys
from datetime import datetime, timezone
import requests
import time
from constants import *
from progress.bar import Bar
import os


def create_folder(path):
    """
    Функция, которая создает папку на яндекс диске
    :param path: str - название папки на яндекс диске
    """
    try:
        response = requests.get(
            f'{Y_URL}?path={path}', headers=headers)
        if response.status_code == 404:
            requests.put(f'{Y_URL}?path={path}', headers=headers)
    except requests.exceptions.ConnectionError:
        print("Error: connection error")
        sys.exit()
    except requests.exceptions.Timeout:
        print("Error: connection timeout")
        sys.exit()
    except requests.exceptions.RequestException as e:
        print("Error: ", e)
        sys.exit()



def delete_backup(backup_name):
    """
    Функция, которая удаляет бэкап с яндекс диска
    :param backup_name: str - название папки с резервным
     сохранением на диске
    <название_папки>_<дата_бэкапа>
    Пример: testFolder_2025_04_11
    """
    try:
        response = requests.get(
            f'{Y_URL}?path={backup_name}', headers=headers)
        if response.status_code == 404:
            print("Error: backup not found")
            sys.exit()
        bar = Bar('Deleting', fill='█', max=300000)

        for _ in range(300000):
            bar.next()
        requests.delete(
            f'{Y_URL}?path={backup_name}&permanently=true',
            headers=headers)
        bar.finish()
        time.sleep(1)
        confirm_response = requests.get(
            f'{Y_URL}?path={backup_name}', headers=headers)

        if confirm_response.status_code == 404:
            print("\nBackup deleted")
            sys.exit(0)
        print("Error: backup doesn't deleted",
              confirm_response.status_code)

    except requests.exceptions.ConnectionError:
        print("Error: connection error")
        sys.exit()
    except requests.exceptions.Timeout:
        print("Error: connection timeout")
        sys.exit()
    except requests.exceptions.RequestException as e:
        print("Error: ", e)
        sys.exit()


def upload(path_to_file, folder_name):
    """
    Функция, которая выгружает файл на яндекс диск
    Если файл был загружен в папку ранее, то проверяем,
    изменяли ли файл с момента его загрузки, если да, то
    загружаем его на диск, нет - не выгружаем, в случае, если
    файла не было ранее на диске, то просто выгражем его туда
    :param path_to_file: str - путь до выгружаемого файла на ПК.
    :param folder_name: str - имя папки на яндекс диске, куда
    будет загружен файл.
    :raises KeyError - не оказалось href, то есть отсутствует ссылка
    на загрузку
    :raise Permission Error - недостаточно прав для получения файла
    на диске локальной машины
    :raise requests.exceptions.Timeout - ловит таймаут при
    отправке запроса на яндекс диск
    """
    file_name = os.path.basename(path_to_file)
    full_path = (
        f'/{folder_name}/{file_name}'.replace("\\", "/"))

    try:
        modification_time_on_pc = datetime.fromtimestamp(
            os.stat(path_to_file).st_mtime, tz=timezone.utc
        )
        check_response = requests.get(f'{Y_URL}?path={full_path}', headers=headers)
        upload_file = True
        if check_response.status_code == 200:
            mod_time_str = requests.get(
                f'{Y_URL}?path={full_path}&fields=modified',
                headers=headers
            ).json().get('modified').replace('T', ' ')[:19]

            if mod_time_str:
                modification_time_on_cloud = datetime.strptime(
                    mod_time_str, "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)
                upload_file = modification_time_on_cloud < modification_time_on_pc


            else:
                upload_file = True

        elif check_response.status_code == 404:
            upload_file = True

        if upload_file:
            response = requests.get(
                f'{Y_URL}/upload?path={full_path}&overwrite=true',
                headers=headers)
            res = response.json()
            with open(path_to_file, "rb") as f:
                requests.put(res['href'], files={'file': f})
    except KeyError:
        print("Error: link doesn't exist")
        sys.exit()
    except PermissionError:
        print("Error: access error")
        sys.exit()
    except requests.exceptions.Timeout:
        print("Error: connection timeout")
        sys.exit()


def backup(load_path):
    """
    Функция, которая делает резервное сохранение папки на
    яндекс диск
    :param load_path: str - путь до нужной папки на ПК
    Пример: D:\testFolder
    """
    if not (os.path.exists(load_path)):
        print("Error: this directory was not found")
        sys.exit()
    folder_name = '{0}_{1}'.format(
        load_path.split('\\')[-1],
        datetime.now().strftime('%Y_%m_%d'))
    create_folder(folder_name)
    all_files = []
    for dir_path, _, files in os.walk(load_path):
        for file in files:
            all_files.append(os.path.join(dir_path, file))

    bar = Bar("Uploading", fill='█', max=len(all_files))

    for dir_path, _, files in os.walk(load_path):
        relative_path = os.path.relpath(dir_path,
                                        load_path).replace('\\', '/')

        if relative_path == '.':
            remote_path = folder_name

        else:
            remote_path = f'{folder_name}/{relative_path}'
            create_folder(remote_path)

        for file in files:
            local_file_path = os.path.join(dir_path,
                                           file).replace('\\', '/')
            upload(local_file_path, remote_path)
            bar.next()

    bar.finish()
    print('Backup complete.')


def download(backup_name, path_on_machine):
    """
    Загружает бэкап на устройство
    :param backup_name: имя резервного сохранения
    :param path_on_machine: путь на устройстве
    в формате "D:\files\backup"
    :raises KeyError - не оказалось href, то есть отсутствует ссылка
    на загрузку
    :raise Permission Error - недостаточно прав для получения файла
    на диске локальной машины
    :raise requests.exceptions.Timeout - ловит таймаут при
    отправке запроса на яндекс диск
    """
    try:
        full_local_path = os.path.join(path_on_machine, backup_name)
        if not os.path.exists(full_local_path):
            os.makedirs(full_local_path, exist_ok=False)
        def count_items(remote_path):
            """
            Функция для подсчета количества файлов на
            диске, используется для progress bar
            :param remote_path:
            """
            result = 0
            response = requests.get(f'{Y_URL}?path={remote_path}&fields=_embedded.items.path, _embedded.items.type', headers=headers)
            items = response.json().get('_embedded', {}).get('items', [])
            for item in items:
                if item['type'] == 'dir':
                    result += count_items(item['path'])
                else:
                    result += 1
            return result

        count_of_files = count_items(backup_name)
        bar = Bar('Downloading', fill='█', max=count_of_files)


        def download_recursive(remote_path):
            """
            Скачивает файл на устройство, в случае, если файл был
            загружен ранее, смотрит, изменился ли файл на облаке,
            в случае, если изменился, то скачиваем на устройство,
            если нет - то не скачиваем, в случае отсутсвия файл на
            устройстве - скачиваем его.
            :param remote_path: Путь до файла на диске
            """
            response = requests.get(
                f'{Y_URL}?path={remote_path}'
                f'&fields=_embedded.items.path,_embedded.items.type',
                headers=headers
            )
            if response.status_code == 404:
                print("Error: backup not found")
                sys.exit()
            items = response.json().get('_embedded', {}).get('items', [])

            for item in items:
                file_path = item['path']
                relative_path = file_path.replace(f'disk:/{backup_name}/', '')
                local_path = os.path.join(str(full_local_path), relative_path).replace('/', '\\')

                if item['type'] == 'dir':
                    if not(os.path.exists(local_path)):
                        os.makedirs(local_path, exist_ok=True)
                    download_recursive(file_path)
                else:
                    mod_time_str = requests.get(
                        f'{Y_URL}?path={file_path}&fields=modified',
                        headers=headers
                    ).json().get('modified').replace('T', ' ')[:19]

                    modification_time_on_cloud = datetime.strptime(mod_time_str, "%Y-%m-%d %H:%M:%S").replace(
                        tzinfo=timezone.utc)

                    if not os.path.exists(local_path):
                        file_download = True
                    else:
                        modification_time_on_pc = datetime.fromtimestamp(
                            os.stat(local_path).st_mtime, tz=timezone.utc
                        )
                        file_download = modification_time_on_cloud > modification_time_on_pc

                    if file_download:
                        download_response = requests.get(
                            f'{Y_URL}/download?path={file_path}',
                            headers=headers
                        )
                        link = download_response.json().get('href')
                        if not link:
                            print(f'Error: download link {file_path} not found')
                            continue
                        bar.next()
                        with requests.get(link, stream=True) as r:
                            with open(local_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)

                        mod_time_epoch = int(modification_time_on_cloud.timestamp())
                        os.utime(local_path, (mod_time_epoch, mod_time_epoch))

        download_recursive(f'disk:/{backup_name}')
        bar.finish()
        print("Download complete!")
        sys.exit(0)

    except requests.exceptions.ConnectionError:
        print("Error: connection error")
        sys.exit()
    except requests.exceptions.Timeout:
        print("Error: connection timeout")
        sys.exit()
    except requests.exceptions.RequestException as e:
        print("Error: ", e)
        sys.exit()