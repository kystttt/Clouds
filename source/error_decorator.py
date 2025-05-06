import time
import functools
import sys


def retry_on_error(max_retries=3, delay=10, prompt_message="Error! Try again? (yes/no)\n"):
    """
    Декоратор, вызывающий исключения для обертки функций
    :param max_retries: int - максимальное количество попыток,
    которое будет предлагать пользователю повторить попытку
    в ожидании исправления ошибки
    :param delay: int - задержка в секундах, сколько времени
    будем ждать перед повторным выпадением ошибки
    :param prompt_message: str - сообщение, которое будет
    выскакивать перед вводом подтверждения повторения или
    отказа
    :return: возвращает декоратор
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            attempt = 0
            while attempt < max_retries:
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    print(f"Error: {e}")
                    attempt += 1
                    if attempt > max_retries:
                        print("Maximum number of retries reached!")
                        sys.exit(1)

                    user_answer = input(prompt_message).strip().lower()
                    if user_answer != "yes":
                        print("Operation stopped")
                        sys.exit(1)
                    else:
                        print(f"Try again after {delay} seconds")
                        time.sleep(delay)
        return wrapper
    return decorator
