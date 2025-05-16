import os
from progress.bar import Bar
import time
import sys
from error_decorator import retry_on_error

class SystemFunction:

    @retry_on_error()
    def delete_backup_on_pc(self, path):
        """
        Удаляет папку с резервной копией на ПК
        :param path: str - путь до директории
        :raises NotADirectoryError: если указанный путь не является
        директорией.
        :raises PermissionError: если у процесса нет прав на удаление
        директории.
        :raises OSError: если возникает другая ошибка, связанная с
        удалением файлов, например, проблемы с файловой системой
        или заблокированные файлы.
        """

        def count_files(directory_path):
            """
            Функция для подсчета файлов бэкапа на ПК
            :param directory_path: str - путь до бэкапа
            :return: возвращает количество файлов в директории
            """
            count = 0
            for dir_path, _, file_names in os.walk(directory_path):
                for _ in file_names:
                    count += 1
            return count

        bar = Bar('Deleting', fill='█', max=count_files(path))

        def remove_recursive(directory_path):
            """
            Удаляет файлы в директории и саму директорию, когда
            она становится пустой
            :param directory_path:
            """
            for dir_path, dir_names, file_names in os.walk(directory_path,
                                                           topdown=False):
                for file_name in file_names:
                    file_path = os.path.join(dir_path, file_name)
                    os.remove(file_path)
                    bar.next()
                    time.sleep(0.3)
                for dir_name in dir_names:
                    os.rmdir(os.path.join(dir_path, dir_name))

            os.rmdir(path)

        remove_recursive(path)
        bar.finish()
        print("Backup deleted!")
        sys.exit(0)
