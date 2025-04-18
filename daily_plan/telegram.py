import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")  # 替换为你的 Telegram Bot Token
CHAT_IDS = [
    7716933130, # mine
]

def send_telegram_message(message, additional_chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    notify_ids = CHAT_IDS + [additional_chat_id]
    merged = list(set(notify_ids))

    print("=========", merged)

    for chat_id in merged:
        data = {"chat_id": chat_id, "text": message}
        try:
            response = requests.post(url, data=data)
            if response.status_code != 200:
                print(f"Telegram 推送失败（chat_id: {chat_id}）：", response.text)
        except Exception as e:
            print(f"Telegram 推送异常（chat_id: {chat_id}）：", e)

        time.sleep(3)


def get_telegram_updates(offset=None):
    params = {"timeout": 10, "offset": offset}
    return requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", params=params).json()

