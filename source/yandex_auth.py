import requests
import os
from constants import*




def yandex_auth():
    print(f"Click on the link and log in: {YANDEX_AUTH_URL}?response_type=code&client_id={Y_CLIENT_ID}")
    auth_code = input("Enter code: ").strip()

    response = requests.post(
        YANDEX_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": Y_CLIENT_ID,
            "client_secret": Y_CLIENT_SECRET
        }
    )

    if response.status_code == 200:
        token = response.json().get("access_token")
        print("Sucess")
        return token
    else:
        print(f"Authorization error: {response.status_code}")
        return None

