import os


START_MESSAGE = """
Welcome to Cloud utility
- help - info about utility's commands
"""

HELP_COMMAND = """
- exit - exit utility
- import - import folder/file from google/yandex cloud
- export - export folder/file from PC to google/yandex cloud
"""

Y_URL = "https://cloud-api.yandex.net/v1/disk/resources"
Y_CLIENT_ID = os.getenv("Y_CLIENT_ID")
Y_CLIENT_SECRET = os.getenv("Y_CLIENT_SECRET")
Y_REDIRECT_URL = "https://oauth.yandex.ru/verification_code"
YANDEX_AUTH_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
Y_AUTH_CODE = os.getenv("Y_AUTH_CODE")
headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {Y_AUTH_CODE}'}

