from abc import ABC, abstractmethod
import os
import sys
from datetime import datetime
from progress.bar import Bar



class CloudAction(ABC):
    @abstractmethod
    def upload(self, path_to_file, folder_name):
        """
        Абстрактный метод для загрузки файла на облако
        :param path_to_file: str - путь до файла на ПК
        :param folder_name: str - название папки, куда выгружаем
        """
        pass


    @abstractmethod
    def create_folder(self, path):
        """
        Абстрактный метод для создания папки на облачном
        хранилище
        :param path: путь до папки
        """
        pass


    def backup(self, load_path):
        """
        Абстрактный метод для создания бэкапа на облачном
        хранилище
        :param load_path: путь откуда мы выгружаем
        """
        pass


    def download(self, backup_name, path_on_machine):
        """
        Абстрактный метод скачивания бэкапа на машину
        :param backup_name: str - название бэкапа
        :param path_on_machine: str - путь на машине
        """
        pass


    @abstractmethod
    def _count_files(self, remote_path):
        """
        Абстрактный метод для подсчета файлов на диске
        :return: количество файлов
        :param int - remote_path: путь на диске
        """
        pass


    @abstractmethod
    def delete_backup_on_cloud(self, backup_name) :
        """
        Абстрактный метод для удаления бэкапа
        :param backup_name: str - название бэкапа
        """
        pass