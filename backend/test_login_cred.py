import os
import requests
import json
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

USERNAME  = os.getenv("STOCKBIT_USERNAME")
PASSWORD  = os.getenv("STOCKBIT_PASSWORD")
PLAYER_ID = os.getenv("STOCKBIT_PLAYER_ID")

LOGIN_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://stockbit.com",
    "Referer": "https://stockbit.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

print(f"Testing login for username: {USERNAME}")
try:
    resp = requests.post(
        "https://exodus.stockbit.com/login/v6/username",
        headers=LOGIN_HEADERS,
        json={
            "user":               USERNAME,
            "password":           PASSWORD,
            "recaptcha_version":  "RECAPTCHA_VERSION_3",
            "player_id":          PLAYER_ID,
        },
    )
    print(f"Status Code: {resp.status_code}")
    data = resp.json()
    print("Full JSON Response:")
    print(json.dumps(data, indent=2))
    
    if "login" in data.get("data", {}):
        print("Login has 'login' token data! SUCCESS!")
    else:
        print("Login does NOT have 'login' token data. It has:", list(data.get("data", {}).keys()))
except Exception as e:
    print(f"Error during login request: {e}")
