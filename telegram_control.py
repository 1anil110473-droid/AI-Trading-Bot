import requests
import os
import time

from db import (
    get_today_trades,
    get_last_10_trades,
    get_open_positions
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================================================
# TELEGRAM DELIVERY ENGINE
# =========================================================

def send(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    for _ in range(3):

        try:

            requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "text": msg
                },
                timeout=15
            )

            return True

        except:

            time.sleep(2)

    return False
