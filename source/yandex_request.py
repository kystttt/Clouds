import sys
import requests
from datetime import datetime
from constants import *
from progress.bar import Bar
import os


def create_folder(path):
    try:
        response = requests.get(f'{Y_URL}?path={path}', headers=headers)
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
    try:
        response = requests.get(f'{Y_URL}?path={backup_name}', headers=headers)
        if response.status_code == 404:
            print("Error: backup not found")
            sys.exit()
        bar = Bar('Deleting', fill='█', max=300000)
        for _ in range(300000):
            bar.next()
        requests.delete(f'{Y_URL}?path={backup_name}&permanently=true', headers=headers)
        print("\nBackup deleted")
        bar.finish()
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


def upload(path_to_file, folder_name):
    file_name = os.path.basename(path_to_file)
    full_path = f'/{folder_name}/{file_name}'.replace("\\", "/")

    try:
        response = requests.get(f'{Y_URL}/upload?path={full_path}&overwrite=true', headers=headers)
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
    folder_name = '{0}_{1}'.format(load_path.split('\\')[-1], datetime.now().strftime('%Y_%m_%d'))
    create_folder(folder_name)
    all_files = []
    for dir_path, _, files in os.walk(load_path):
        for file in files:
            all_files.append(os.path.join(dir_path, file))

    bar = Bar("Uploading", fill='█', max=len(all_files))

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
            bar.next()

    bar.finish()
    print('Backup complete.')
