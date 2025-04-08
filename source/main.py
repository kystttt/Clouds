from constants import *
from yandex_request import backup


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
                pass
            case "export":
                backup(input("Enter load path: ").strip())

            case _:
                print("Invalid mode")



if __name__ == '__main__':
    main()