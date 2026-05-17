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

LAST_UPDATE_ID = None

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

# =========================================================
# TELEGRAM COMMAND HANDLER
# =========================================================

def handle_command(message):

    text = message["text"]

    # =============================================
    # TODAY TRADES
    # =============================================

    if text == "/today":

        trades = get_today_trades()

        if not trades:

            send("❌ No trades today")
            return

        msg = "📊 TODAY TRADE REPORT\n\n"

        for t in trades:

            msg += f"""

{t[0]}
{t[1]}

💰 Price: ₹{t[2]}
📦 Qty: {t[3]}
💵 PNL: ₹{t[4]}
🧠 {t[5]}
🕒 {t[6]}

"""

        send(msg)

    # =============================================
    # LAST 10 TRADES
    # =============================================

    elif text == "/last10":

        trades = get_last_10_trades()

        if not trades:

            send("❌ No trade history")
            return

        msg = "📈 LAST 10 TRADES\n\n"

        for t in trades:

            msg += f"""

{t[0]}
{t[1]}

💰 ₹{t[2]}
📦 Qty: {t[3]}
💵 PNL: ₹{t[4]}
🕒 {t[6]}

"""

        send(msg)

    # =============================================
    # OPEN POSITIONS
    # =============================================

    elif text == "/openpositions":

        positions = get_open_positions()

        if not positions:

            send("❌ No open positions")
            return

        msg = "📦 OPEN POSITIONS\n\n"

        for p in positions:

            msg += f"""

{p[0]}

💰 Buy Price: ₹{p[1]}
📦 Qty: {p[2]}
📈 Highest: ₹{p[3]}

"""

        send(msg)

# =========================================================
# TELEGRAM COMMAND LISTENER
# =========================================================

def listen_telegram():

    global LAST_UPDATE_ID

    while True:

        try:

            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

            response = requests.get(url).json()

            if response["ok"]:

                for update in response["result"]:

                    update_id = update["update_id"]

                    if LAST_UPDATE_ID is not None:

                        if update_id <= LAST_UPDATE_ID:
                            continue

                    LAST_UPDATE_ID = update_id

                    if "message" not in update:
                        continue

                    message = update["message"]

                    if "text" not in message:
                        continue

                    handle_command(message)

            time.sleep(5)

        except:

            time.sleep(5)
