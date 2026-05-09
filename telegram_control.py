import requests
import os
import time

TOKEN = os.getenv("TELEGRAM_TOKEN")

CHAT_ID = os.getenv("CHAT_ID")

def send(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {

        "chat_id": CHAT_ID,
        "text": msg

    }

    for _ in range(3):

        try:

            r = requests.post(
                url,
                data=payload,
                timeout=15
            )

            if r.status_code == 200:

                return True

        except:

            time.sleep(2)

    return False
