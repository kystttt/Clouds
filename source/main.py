from constants import *
from yandex_request import backup, delete_backup
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
            sys.exit(0)
        mode = sys.argv[1].strip()

        if  mode == "export" and not(os.path.exists(sys.argv[2])):
            print("Error: this directory was not found")
            sys.exit(0)

        if mode == "export":
            backup(sys.argv[2].strip())
        elif mode == "import":
            pass
        elif mode == "delete":
            delete_backup(sys.argv[2].strip())
        else:
            print("Invalid mode")
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == '__main__':
    main()
