import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot API bilgileri
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Telegram mesajı başarıyla gönderildi!")
        else:
            print(f"Hata: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Telegram mesajı gönderilirken hata oluştu: {e}")
