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

Y_URL = "https://disk.yandex.ru/client/disk"
Y_CLIENT_ID =  "ffb15f5d11ca48b6a2b6f134a0f33502"#os.getenv("Y_CLIENT_ID")
Y_CLIENT_SECRET = "9765ef160ebc4ac5a6b447f1dc557037"         #os.getenv("Y_CLIENT_SECRET")
Y_REDIRECT_URL = "https://oauth.yandex.ru/verification_code"
YANDEX_AUTH_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
