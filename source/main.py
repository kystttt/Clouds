from yandex_request import backup, delete_backup_on_cloud,download, delete_backup_on_pc
import sys


def main():
    """
        Функция, реализующая логику утилиты:
        import - импортировать папку/файл с облачного хранилища
        export - загрузить папку/файл в облачное хранилище
        delete - удалить резервное сохранение с диска
        remove - удалить резервное сохранение с ПК
        """
    try:
        if len(sys.argv) < 3:
            print("Error: count of arguments should be 3")
            sys.exit()
        mode = sys.argv[1].strip()

        if mode == "upload":
            backup(sys.argv[2].strip())
        elif mode == "download":
            download(sys.argv[2].strip(), sys.argv[3].strip())
        elif mode == "delete":
            delete_backup_on_cloud(sys.argv[2].strip())
        elif mode == "remove":
            delete_backup_on_pc(sys.argv[2].strip())
        else:
            print("Invalid mode")

    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == '__main__':
    main()
