from progress.bar import Bar
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from error_decorator import retry_on_error
import sys
import os
from datetime import datetime, timezone
import time
from threading import Lock


class YandexAction:
    def __init__(self, y_url, headers):
        self.Y_URL = y_url
        self.headers = headers


    @retry_on_error()
    def create_folder(self, path):
        """
           Метод, который создает папку на яндекс диске
           :param path: str - название папки на яндекс диске
           """
        response = requests.get(
            f'{self.Y_URL}?path={path}', headers=self.headers)
        if response.status_code == 404:
            requests.put(f'{self.Y_URL}?path={path}', headers=self.headers)


    @retry_on_error()
    def delete_backup_on_cloud(self, backup_name):
        """
        Метод, который удаляет бэкап с яндекс диска
        :param backup_name: str - название папки с резервным
         сохранением на диске
        <название_папки>_<дата_бэкапа>
        Пример: testFolder_2025_04_11
        """
        response = requests.get(
            f'{self.Y_URL}?path={backup_name}', headers=self.headers)
        if response.status_code == 404:
            print("Error: backup not found")
            sys.exit(1)
        counter = self._count_files(backup_name)
        bar = Bar('Deleting', fill='█', max=counter)

        for _ in range(counter):
            bar.next()
            time.sleep(0.8)
        requests.delete(
            f'{self.Y_URL}?path={backup_name}&permanently=true',
            headers=self.headers)
        bar.finish()
        time.sleep(1)
        confirm_response = requests.get(
            f'{self.Y_URL}?path={backup_name}', headers=self.headers)

        if confirm_response.status_code == 404:
            print("Backup deleted!")
            sys.exit(0)
        print("Error: backup doesn't deleted",
              confirm_response.status_code)


    @retry_on_error()
    def upload(self, path_to_file, folder_name):
        """
        Метод, который выгружает файл на яндекс диск
        Если файл был загружен в папку ранее, то проверяем,
        изменяли ли файл с момента его загрузки, если да, то
        загружаем его на диск, нет - не выгружаем, в случае, если
        файла не было ранее на диске, то просто выгражем его туда
        :param path_to_file: str - путь до выгружаемого файла на ПК.
        :param folder_name: str - имя папки на яндекс диске, куда
        будет загружен файл.
        :raises KeyError - не оказалось href, то есть отсутствует ссылка
        на загрузку
        :raises Permission Error - недостаточно прав для получения
        файла на диске локальной машины
        :raises requests.exceptions.Timeout - ловит таймаут при
        отправке запроса на яндекс диск
        """
        file_name = os.path.basename(path_to_file)
        full_path = (
            f'/{folder_name}/{file_name}'.replace("\\", "/"))

        modification_time_on_pc = datetime.fromtimestamp(
            os.stat(path_to_file).st_mtime, tz=timezone.utc
        )
        check_response = requests.get(f'{self.Y_URL}?path={full_path}',
                                      headers=self.headers)
        upload_file = True
        if check_response.status_code == 200:
            mod_time_str = requests.get(
                f'{self.Y_URL}?path={full_path}&fields=modified',
                headers=self.headers
            ).json().get('modified').replace('T', ' ')[:19]

            if mod_time_str:
                modification_time_on_cloud = datetime.strptime(
                    mod_time_str, "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)
                upload_file = (modification_time_on_cloud
                               < modification_time_on_pc)
            else:
                upload_file = True

        elif check_response.status_code == 404:
            upload_file = True

        if upload_file:
            response = requests.get(
                f'{self.Y_URL}/upload?path={full_path}&overwrite=true',
                headers=self.headers)
            res = response.json()
            with open(path_to_file, "rb") as f:
                requests.put(res['href'], files={'file': f})


    @retry_on_error()
    def _count_files(self, remote_path):
        """
        Метод для подсчета количества файлов на
        диске, используется для progress bar
        :param remote_path:
        :return возвращает количество файлов на диске
        """
        result = 0
        response = requests.get(f'{self.Y_URL}?path='
                                f'{remote_path}&fields=_embedded.items.path, '
                                f'_embedded.items.type', headers=self.headers)
        items = response.json().get('_embedded', {}).get('items', [])
        for item in items:
            if item['type'] == 'dir':
                result += self._count_files(item['path'])
            else:
                result += 1
        return result


    @retry_on_error()
    def download(self, backup_name, path_on_machine):
        """
        Скачивает файл на устройство, в случае, если файл был
        загружен ранее, смотрит, изменился ли файл на облаке,
        в случае, если изменился, то скачиваем на устройство,
        если нет - то не скачиваем, в случае отсутсвия файл на
        устройстве - скачиваем его.
        :param backup_name: str - название бэкапа
        :param path_on_machine: str - Путь до файла на диске
         """
        full_local_path = os.path.join(path_on_machine, backup_name)
        if not os.path.exists(full_local_path):
            os.makedirs(full_local_path, exist_ok=False)

        files_to_download = []

        def collect_files(remote_path, local_base):
            response = requests.get(
                f'{self.Y_URL}?path={remote_path}'
                f'&fields=_embedded.items.path,_embedded.items.type',
                headers=self.headers
            )
            if response.status_code == 404:
                print("Error: backup not found")
                sys.exit(1)
            items = response.json().get('_embedded', {}).get('items', [])
            for item in items:
                file_path = item['path']
                relative_path = file_path.replace(f'disk:/{backup_name}', '').lstrip('/')
                local_path = os.path.join(local_base, relative_path)
                if item['type'] == 'dir':
                    if not os.path.exists(local_path):
                        os.makedirs(local_path, exist_ok=True)
                    collect_files(file_path, local_base)
                else:
                    mod_time_str = requests.get(
                        f'{self.Y_URL}?path={file_path}&fields=modified',
                        headers=self.headers
                    ).json().get('modified').replace('T', ' ')[:19]
                    modification_time_on_cloud = datetime.strptime(
                        mod_time_str, "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=timezone.utc)
                    if not os.path.exists(local_path):
                        file_download = True
                    else:
                        modification_time_on_pc = datetime.fromtimestamp(
                            os.stat(local_path).st_mtime, tz=timezone.utc
                        )
                        file_download = modification_time_on_cloud > modification_time_on_pc
                    if file_download:
                        files_to_download.append((file_path, local_path, modification_time_on_cloud))

        collect_files(f'disk:/{backup_name}', full_local_path)
        if not files_to_download:
            print("All files are up to date.")
            sys.exit(0)

        bar = Bar('Downloading', fill='█', max=len(files_to_download))
        bar_lock = Lock()

        def download_file(remote_file_path, local_file_path, cloud_mod_time):
            try:
                download_response = requests.get(
                    f'{self.Y_URL}/download?path={remote_file_path}',
                    headers=self.headers
                )
                link = download_response.json().get('href')
                if not link:
                    print(f'Error: download link {remote_file_path} not found')
                    return

                with requests.get(link, stream=True) as r:
                    with open(local_file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                mod_time_epoch = int(cloud_mod_time.timestamp())
                os.utime(local_file_path, (mod_time_epoch, mod_time_epoch))

            finally:
                with bar_lock:
                    bar.next()

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(download_file, *args) for args in files_to_download]
            for _ in as_completed(futures):
                pass
        bar.finish()
        print("Download completed!")
        sys.exit(0)


    def backup(self, load_path):
        """
        Реализация резервного копирования
        :param load_path: str - путь до папки для бэкапа
        Пример: D:\testFolder
        """
        if not os.path.exists(load_path):
            print("Error: this directory was not found")
            sys.exit(1)

        folder_name = '{0}_{1}'.format(
            os.path.basename(load_path),
            datetime.now().strftime('%Y_%m_%d')
        )
        self.create_folder(folder_name)
        all_files = []
        for dir_path, _, files in os.walk(load_path):
            for file in files:
                all_files.append(os.path.join(dir_path, file))
        bar = Bar("Uploading", fill='█', max=len(all_files))
        bar_lock = Lock()

        def upload_process(file_path):
            relative_path = os.path.relpath(os.path.dirname(file_path), load_path).replace('\\', '/')
            remote_path = folder_name if relative_path == '.' else f'{folder_name}/{relative_path}'
            if relative_path != '.':
                self.create_folder(remote_path)
            self.upload(file_path, remote_path)
            with bar_lock:
                bar.next()

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(upload_process, file) for file in all_files]
            for _ in as_completed(futures):
                pass

        bar.finish()
        print('Backup completed!')
        sys.exit(0)


    @retry_on_error()
    def list_of_files_on_backup(self, backup_name):
        """
        Метод, который выводит листинг файлов и папок в бэкапе
        :param backup_name: str - название бэкапа на облаке
        """
        print(f'{backup_name}: ')

        def print_recursive(folder, indent=1):
            response = requests.get(
                f'{self.Y_URL}?path={folder}&fields=_embedded.items.name,_embedded.items.type,_embedded.items.path',
                headers=self.headers
            )
            items = response.json().get('_embedded', {}).get('items', [])
            for item in items:
                if item['type'] == 'dir':
                    print(' ' * indent + f"{item['name']}:")
                    print_recursive(item['path'], indent + 2)
                else:
                    print(' ' * indent + item['name'])

        print_recursive(backup_name)
