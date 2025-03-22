from constants import *
from yandex_request import upload
from yandex_auth import yandex_auth

def main():
    """
        Функция, реализующая логику утилиты:
        help - справка по утилите
        exit - выход из утилиты
        import - импортировать папку/файл с облачного хранилища
        export - загрузить папку/файл в облачное хранилище

        """
    print(START_MESSAGE)

    while True:
        mode = input("Enter mode? which start work: ").strip()
        match mode:
            case "help":
                print(HELP_COMMAND)
            case "exit":
                print("Exiting...")
                break
            case "import":
                token = yandex_auth()
                headers = {"Authorization": f"OAuth {token}"}
                path = input("Enter the file path: ").strip()
                path_on_cloud = "backup1"
                upload(token, path, path_on_cloud, headers)
            case "export":
                pass

            case _:
                print("Invalid mode")



if __name__ == '__main__':
    main()