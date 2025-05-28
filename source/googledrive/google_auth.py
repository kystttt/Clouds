from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from source.constants import scopes
import os
import sys


def oauth_to_drive():
    """
    Функция для авторизации пользователя через гугл аккаунт
    :return: возвращает собранный токен
    """
    creds = None
    token_path = "..token.json"
    credentials_path = "../source/client_secret.json"

    try:
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, scopes
                )
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        return build("drive", "v3", credentials=creds)

    except Exception as e:
        print(f"Google OAuth error: {e}")
        sys.exit(1)
