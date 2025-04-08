import requests
from datetime import datetime
from constants import*
import os


def create_folder(path):
    response = requests.get(f'{Y_URL}?path={path}', headers=headers)
    if response.status_code == 404:
        res = requests.put(f'{Y_URL}?path={path}', headers=headers)
        print("Folder created:  ", res.status_code)
    else:
        print("Error:  ", response.status_code)

def upload(path_to_file, folder_name):
    file_name = os.path.basename(path_to_file)
    full_path = f'/{folder_name}/{file_name}'.replace("\\", "/")

    res = requests.get(f'{Y_URL}/upload?path={full_path}&overwrite=true', headers=headers).json()
    with open(path_to_file, "rb") as f:
        try:
            requests.put(res['href'], files={'file': f})
        except KeyError:
            print(res)


def backup(load_path):
    folder_name = '{0}_{1}'.format(load_path.split('\\')[-1], datetime.now().strftime('%Y%m%d'))
    create_folder(folder_name)

    for dir_path, _, files in os.walk(load_path):
        relative_path = os.path.relpath(dir_path, load_path).replace('\\', '/')
        if relative_path == '.':
            remote_path = folder_name

        else:
            remote_path = f'{folder_name}/{relative_path}'
            create_folder(remote_path)

        for file in files:
            local_file_path = os.path.join(dir_path, file).replace('\\', '/')
            upload(local_file_path, remote_path)
    print('Backup complete.')