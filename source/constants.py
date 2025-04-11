from secret_keys import *


Y_URL = "https://cloud-api.yandex.net/v1/disk/resources"
Y_REDIRECT_URL = "https://oauth.yandex.ru/verification_code"
YANDEX_AUTH_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {Y_AUTH_CODE}'}

