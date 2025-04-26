from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from  constants import scopes
import sys
from googleapiclient.errors import HttpError
from secret_keys import G_CREDENTIALS_JSON, G_TOKEN_JSON




def oauth_to_drive():
    """
    Авторизация пользователя для работы с Google Drive Api

    :return:
    """
    creds = None
    try:
        if G_TOKEN_JSON:
            creds = Credentials.from_authorized_user_info(G_TOKEN_JSON, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(G_CREDENTIALS_JSON, scopes)
                creds = flow.run_local_server(port=0)

        return build("drive", "v3", credentials=creds)

    except HttpError as e:
        print(f"Error: {e}")
        sys.exit()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit()
