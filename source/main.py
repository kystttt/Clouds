from source.yandexdrive.YandexAction import YandexAction
from source.googledrive.GoogleAction import GoogleAction
from source.constants import Y_URL, headers
import sys
from source.SystemFunction import SystemFunction


def main():
    """
    Функция, реализующая логику утилиты:
    y_download/g_download - импортировать папку/файл с облачного хранилища
    y_upload/g_upload - загрузить папку/файл в облачное хранилище
    y_delete - удалить резервное сохранение с яндекс диска
    g_delete - удалить резервное сохранение с гугл диска
    delete - удалить резервное сохранение с ПК
    y_list_of_files/g_list_of_files - листинг файлов в бэкапе на облаке
    """
    try:
        system_function = SystemFunction()
        yandex_action = YandexAction(Y_URL, headers)
        google_action = GoogleAction()
        if len(sys.argv) < 3:
            print("Error: count of arguments should be 3")
            sys.exit(1)
        mode = sys.argv[1].strip()

        if mode == "y_upload":
            yandex_action.backup(sys.argv[2].strip())
        elif mode == "y_download":
            if len(sys.argv) < 4:
                print("Error: count of arguments should be 4")
                sys.exit(1)
            yandex_action.download(sys.argv[2].strip(), sys.argv[3].strip())
        elif mode == "y_delete":
            yandex_action.delete_backup_on_cloud(sys.argv[2].strip())
        elif mode == "y_list_of_files":
            yandex_action.list_of_files_on_backup(sys.argv[2].strip())
        elif mode == "delete":
            system_function.delete_backup_on_pc(sys.argv[2].strip())
        elif mode == "g_upload":
            google_action.backup(sys.argv[2].strip())
        elif mode == "g_download":
            if len(sys.argv) < 4:
                print("Error: count of arguments should be 4")
                sys.exit(1)
            google_action.download(sys.argv[2].strip(), sys.argv[3].strip())
        elif mode == "g_delete":
            google_action.delete_backup_on_cloud(sys.argv[2].strip())
        elif mode == "g_list_of_files":
            google_action.list_of_files_on_backup(sys.argv[2].strip())
        else:
            print("Invalid mode")

    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
