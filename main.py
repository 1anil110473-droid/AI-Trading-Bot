import yfinance as yf
import pandas as pd
import time
import traceback
from datetime import datetime
import pytz

from db import init_db, save_trade
from ai import weights
from risk import position_size
from market import market_trend
from strategy import apply_strategy
from telegram_control import send
from broker import place_order

# =========================================================
# CONFIG
# =========================================================

CAPITAL = 200000
DAILY_TARGET = 1000
MAX_OPEN_POSITIONS = 5

TRAILING_STOPLOSS_PERCENT = 1.5
TARGET_PERCENT = 3
STOPLOSS_PERCENT = -2
PARTIAL_BOOKING_PERCENT = 2

MARKET_CRASH_THRESHOLD = -1.5

# ==========================================
# IMPORTANT CHANGE
# ==========================================

SCAN_INTERVAL = 60           # FAST SCAN
HEARTBEAT_INTERVAL = 1800    # 30 MIN

TIMEZONE = pytz.timezone("Asia/Kolkata")

# =========================================================
# GLOBALS
# =========================================================

positions = {}
daily_profit = 0

last_heartbeat_time = 0
last_trend_time = 0

# =========================================================
# STOCKS
# =========================================================

STOCKS = [

    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "SBIN.NS",

    "TCS.NS",
    "INFY.NS",
    "WIPRO.NS",

    "RELIANCE.NS",
    "TATASTEEL.NS",
    "HINDZINC.NS",

    "HINDCOPPER.NS",
    "SUNPHARMA.NS",
    "DRREDDY.NS",

    "CIPLA.NS",
    "COFORGE.NS",
    "TRENT.NS"

]

# =========================================================
# DB INIT
# =========================================================

init_db()

# =========================================================
# START MESSAGE
# =========================================================

send(f"""

🚀 V40 INSTITUTIONAL AI ENGINE STARTED

✅ AI ENGINE ACTIVE
✅ FAST EXIT SYSTEM ACTIVE
✅ SMART HEARTBEAT ACTIVE
✅ TRAILING STOPLOSS ACTIVE
✅ MARKET TREND FILTER ACTIVE
✅ MULTI STOCK SCANNER ACTIVE
✅ DATABASE CONNECTED
✅ PAPER TRADING MODE ACTIVE

💰 CAPITAL:
₹{CAPITAL}

🎯 DAILY TARGET:
₹{DAILY_TARGET}

📦 MAX OPEN POSITIONS:
{MAX_OPEN_POSITIONS}

⚡ SCAN SPEED:
{SCAN_INTERVAL} sec

🛡 SYSTEM:
INSTITUTIONAL GRADE

""")

# =========================================================
# MARKET HOURS
# =========================================================

def market_open():

    now = datetime.now(TIMEZONE)

    if now.weekday() >= 5:
        return False

    current = now.strftime("%H:%M")

    return "09:15" <= current <= "15:30"

# =========================================================
# MARKET CRASH
# =========================================================

def market_crash():

    try:

        nifty = yf.download(
            "^NSEI",
            period="2d",
            interval="15m",
            progress=False,
            auto_adjust=True
        )

        if nifty.empty:
            return False

        close = float(nifty["Close"].iloc[-1])
        prev = float(nifty["Close"].iloc[-2])

        change = ((close - prev) / prev) * 100

        return change <= MARKET_CRASH_THRESHOLD

    except:
        return False

# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        now = datetime.now(TIMEZONE)

        # =====================================================
        # MARKET CLOSED
        # =====================================================

        if not market_open():

            hour = now.hour

            if hour >= 16 or hour < 7:

                print("Night Deep Sleep")
                time.sleep(21600)

            else:

                print("Waiting Market Open")
                time.sleep(300)

            continue

        # =====================================================
        # DAILY TARGET
        # =====================================================

        if daily_profit >= DAILY_TARGET:

            send(f"""

🎯 DAILY TARGET ACHIEVED

💰 TOTAL PROFIT:
₹{round(daily_profit,2)}

🛑 NEW TRADES STOPPED

""")

            time.sleep(1800)
            continue

        # =====================================================
        # MARKET CRASH
        # =====================================================

        if market_crash():

            send("""

🚨 MARKET CRASH DETECTED

🛑 NEW TRADES BLOCKED

🛡 SAFETY MODE ACTIVE

""")

            time.sleep(1800)
            continue

        # =====================================================
        # MARKET TREND UPDATE
        # EVERY 30 MIN
        # =====================================================

        current_time = time.time()

        if current_time - last_trend_time > 1800:

            trend = market_trend()

            send(f"""

📊 MARKET TREND UPDATE

📈 CURRENT TREND:
{trend}

🧠 AI TREND FILTER ACTIVE

""")

            last_trend_time = current_time

        # =====================================================
        # STOCK SCAN
        # =====================================================

        for stock in STOCKS:

            try:

                df = yf.download(
                    stock,
                    period="5d",
                    interval="15m",
                    auto_adjust=True,
                    progress=False
                )

                if df.empty or len(df) < 100:
                    continue

                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df = df.dropna()

                score, reasons = apply_strategy(df, weights)

                confidence = min(score, 100)

                price = round(float(df["Close"].iloc[-1]), 2)

                qty = position_size(
                    CAPITAL,
                    confidence,
                    price
                )

                # =================================================
                # ENTRY
                # =================================================

                if (

                    confidence >= 70
                    and stock not in positions
                    and len(positions) < MAX_OPEN_POSITIONS

                ):

                    positions[stock] = {

                        "buy_price": price,
                        "qty": qty,
                        "highest_price": price,
                        "partial_booked": False

                    }

                    place_order(stock, "BUY", qty)

                    save_trade(
                        stock,
                        "BUY",
                        price,
                        qty,
                        0,
                        "AI BUY"
                    )

                    send(f"""

🟢 STRONG AI BUY SIGNAL

📈 STOCK:
{stock}

💰 ENTRY:
₹{price}

📦 QTY:
{qty}

🧠 CONFIDENCE:
{confidence}/100

🎯 TARGET:
+3%

🛑 STOPLOSS:
-2%

🛡 TRAILING STOP:
ACTIVE

""")

                # =================================================
                # POSITION MANAGEMENT
                # =================================================

                if stock in positions:

                    bp = positions[stock]["buy_price"]
                    qty = positions[stock]["qty"]

                    # =============================================
                    # HIGHEST PRICE TRACK
                    # =============================================

                    if price > positions[stock]["highest_price"]:

                        positions[stock]["highest_price"] = price

                    highest = positions[stock]["highest_price"]

                    pnl_percent = round(
                        ((price - bp) / bp) * 100,
                        2
                    )

                    pnl_amount = round(
                        ((price - bp) * qty),
                        2
                    )

                    trailing_sl = round(
                        highest * (
                            1 - TRAILING_STOPLOSS_PERCENT / 100
                        ),
                        2
                    )

                    # =============================================
                    # PARTIAL BOOKING
                    # =============================================

                    if (

                        pnl_percent >= PARTIAL_BOOKING_PERCENT
                        and not positions[stock]["partial_booked"]

                    ):

                        positions[stock]["partial_booked"] = True

                        send(f"""

🟡 PARTIAL PROFIT BOOKING

📈 STOCK:
{stock}

💰 PRICE:
₹{price}

📊 RETURN:
{pnl_percent}%

💵 PNL:
₹{pnl_amount}

""")

                    # =============================================
                    # EXIT CONDITIONS
                    # =============================================

                    exit_reason = None

                    if pnl_percent >= TARGET_PERCENT:

                        exit_reason = "TARGET ACHIEVED"

                    elif pnl_percent <= STOPLOSS_PERCENT:

                        exit_reason = "STOPLOSS HIT"

                    elif (

                        price <= trailing_sl
                        and pnl_percent > 0

                    ):

                        exit_reason = "TRAILING STOPLOSS HIT"

                    # =============================================
                    # EXIT
                    # =============================================

                    if exit_reason:

                        daily_profit += pnl_amount

                        place_order(stock, "SELL", qty)

                        save_trade(
                            stock,
                            "SELL",
                            price,
                            qty,
                            pnl_amount,
                            exit_reason
                        )

                        send(f"""

🔴 POSITION EXIT

📉 STOCK:
{stock}

💰 EXIT PRICE:
₹{price}

💵 PNL:
₹{pnl_amount}

📊 RETURN:
{pnl_percent}%

🧠 EXIT REASON:
{exit_reason}

💰 DAILY PROFIT:
₹{round(daily_profit,2)}

""")

                        del positions[stock]

            except Exception as stock_error:

                print(stock, stock_error)

                continue

        # =====================================================
        # HEARTBEAT
        # EVERY 30 MIN
        # =====================================================

        if current_time - last_heartbeat_time > HEARTBEAT_INTERVAL:

            send(f"""

💓 BOT HEARTBEAT

✅ BOT RUNNING OK
✅ AI ENGINE ACTIVE
✅ MARKET SCANNER ACTIVE
✅ DATABASE CONNECTED

💰 DAILY PROFIT:
₹{round(daily_profit,2)}

📊 OPEN POSITIONS:
{len(positions)}

📈 TRACKING STOCKS:
{len(STOCKS)}

🚀 SYSTEM STATUS:
STABLE

""")

            last_heartbeat_time = current_time

        # =====================================================
        # WAIT
        # =====================================================

        time.sleep(SCAN_INTERVAL)

    except Exception as e:

        send(f"""

🚨 MAIN LOOP ERROR

❌ ERROR:
{str(e)}

📌 TRACEBACK:

{traceback.format_exc()}

🛡 AUTO RECOVERY ACTIVE

""")

        time.sleep(60)
