import time
import functools
import os
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

                    if os.environ.get("UNIT_TEST_MODE") == "1":
                        raise

                    interactive = getattr(self, "interactive", True)
                    if not interactive or attempt > max_retries:
                        print("Operation stopped")
                        return

                    user_answer = input(prompt_message).strip().lower()
                    if user_answer != "yes":
                        print("Operation stopped")
                        return
                    else:
                        print(f"Try again after {delay} seconds")
                        time.sleep(delay)
        return wrapper
    return decorator
