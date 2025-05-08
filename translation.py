import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://openl-translate.p.rapidapi.com/translate"
API_KEY = os.getenv("OPENL_API_KEY")


def translate_text(text, target="en"):
    payload = {"target_lang": target, "text": text}
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "openl-translate.p.rapidapi.com",
        "Content-Type": "application/json",
    }

    response = requests.post(API_URL, json=payload, headers=headers)
    return response.json()["translatedText"]
