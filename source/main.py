from yandex_request import backup, delete_backup,download
import sys


def main():
    """
        Функция, реализующая логику утилиты:
        import - импортировать папку/файл с облачного хранилища
        export - загрузить папку/файл в облачное хранилище
        """
    try:
        if len(sys.argv) < 3:
            print("Error: count of arguments should be 3")
            sys.exit()
        mode = sys.argv[1].strip()

        if mode == "export":
            backup(sys.argv[2].strip())
        elif mode == "import":
            download(sys.argv[2].strip(), sys.argv[3].strip())
        elif mode == "delete":
            delete_backup(sys.argv[2].strip())
        else:
            print("Invalid mode")

    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == '__main__':
    main()
