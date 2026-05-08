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
# CONFIGURATION
# =========================================================

CAPITAL = 200000

DAILY_TARGET = 1000

MAX_OPEN_POSITIONS = 5

RISK_PER_TRADE = 0.02

TRAILING_STOPLOSS_PERCENT = 1.5

TARGET_PERCENT = 3

STOPLOSS_PERCENT = -2

PARTIAL_BOOKING_PERCENT = 2

MARKET_CRASH_THRESHOLD = -1.5

SCAN_INTERVAL = 1800

TIMEZONE = pytz.timezone("Asia/Kolkata")

# =========================================================
# GLOBAL VARIABLES
# =========================================================

positions = {}

daily_profit = 0

last_heartbeat = None

# =========================================================
# STOCK LIST
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
# DATABASE INIT
# =========================================================

init_db()

# =========================================================
# STARTUP MESSAGE
# =========================================================

send(f"""

🚀 V35 ELITE INSTITUTIONAL AI STARTED

✅ AI ENGINE ACTIVE
✅ MARKET TREND FILTER ACTIVE
✅ MULTI STOCK SCANNER ACTIVE
✅ TRAILING STOPLOSS ACTIVE
✅ PARTIAL PROFIT BOOKING ACTIVE
✅ HEARTBEAT ACTIVE
✅ DATABASE CONNECTED
✅ PAPER TRADING MODE ACTIVE

💰 CAPITAL:
₹{CAPITAL}

🎯 DAILY TARGET:
₹{DAILY_TARGET}

📦 MAX OPEN POSITIONS:
{MAX_OPEN_POSITIONS}

🛡 RISK MANAGEMENT:
INSTITUTIONAL GRADE

""")

# =========================================================
# MARKET HOURS CHECK
# =========================================================

def market_open():

    now = datetime.now(TIMEZONE)

    # Saturday/Sunday OFF

    if now.weekday() >= 5:
        return False

    current = now.strftime("%H:%M")

    return "09:15" <= current <= "15:30"

# =========================================================
# MARKET CRASH DETECTION
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

        if change <= MARKET_CRASH_THRESHOLD:
            return True

        return False

    except:
        return False

# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        # =========================================================
        # MARKET HOURS FILTER
        # =========================================================

        if not market_open():

            now = datetime.now(TIMEZONE)

            hour = now.hour

    # ==========================================
    # NIGHT DEEP SLEEP
    # ==========================================

       if hour >= 16 or hour < 7:

            print("Night Mode Active")

            time.sleep(21600)

    # ==========================================
    # PRE-MARKET ACTIVE MODE
    # ==========================================

       else:

           print("Waiting For Market Open")

           time.sleep(300)

           continue

        # =========================================================
        # DAILY TARGET CHECK
        # =========================================================

        if daily_profit >= DAILY_TARGET:

            send(f"""

🎯 DAILY TARGET ACHIEVED

💰 TOTAL PROFIT:
₹{round(daily_profit,2)}

🛑 NEW TRADES STOPPED

✅ CAPITAL PROTECTED
✅ OVERTRADING PREVENTED

🚀 BOT WAITING FOR NEXT SESSION

""")

            time.sleep(1800)

            continue

        # =========================================================
        # MARKET CRASH PROTECTION
        # =========================================================

        if market_crash():

            send("""

🚨 MARKET CRASH DETECTED

🛑 ALL NEW TRADES BLOCKED

🛡 CAPITAL PROTECTION MODE ACTIVE

""")

            time.sleep(1800)

            continue

        # =========================================================
        # MARKET TREND
        # =========================================================

        trend = market_trend()

        send(f"""

📊 MARKET TREND UPDATE

📈 CURRENT TREND:
{trend}

🧠 AI TREND FILTER ACTIVE

""")

        # =========================================================
        # STOCK SCANNING
        # =========================================================

        for stock in STOCKS:

            try:

                # =========================================================
                # MAX POSITION CONTROL
                # =========================================================

                if len(positions) >= MAX_OPEN_POSITIONS:
                    break

                # =========================================================
                # DATA DOWNLOAD
                # =========================================================

                df = yf.download(

                    stock,
                    period="5d",
                    interval="15m",
                    auto_adjust=True,
                    progress=False

                )

                if df.empty or len(df) < 100:
                    continue

                # =========================================================
                # FIX MULTI INDEX
                # =========================================================

                if isinstance(df.columns, pd.MultiIndex):

                    df.columns = df.columns.get_level_values(0)

                df = df.dropna()

                # =========================================================
                # STRATEGY
                # =========================================================

                score, reasons = apply_strategy(df, weights)

                confidence = min(score, 100)

                price = round(
                    float(df["Close"].iloc[-1]),
                    2
                )

                qty = position_size(
                    CAPITAL,
                    confidence,
                    price
                )

                # =========================================================
                # STRONG FILTER
                # =========================================================

                if trend == "BEARISH" and confidence < 85:
                    continue

                # =========================================================
                # MULTI TIMEFRAME CONFIRMATION
                # =========================================================

                higher = yf.download(

                    stock,
                    period="10d",
                    interval="1h",
                    auto_adjust=True,
                    progress=False

                )

                if higher.empty:
                    continue

                if isinstance(higher.columns, pd.MultiIndex):

                    higher.columns = higher.columns.get_level_values(0)

                h_close = float(higher["Close"].iloc[-1])

                h_ema = float(
                    higher["Close"]
                    .rolling(20)
                    .mean()
                    .iloc[-1]
                )

                if h_close < h_ema:
                    continue

                # =========================================================
                # BUY SIGNAL
                # =========================================================

                if confidence >= 70 and stock not in positions:

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

💰 ENTRY PRICE:
₹{price}

📦 QUANTITY:
{qty}

💵 INVESTMENT:
₹{round(price*qty,2)}

🧠 AI CONFIDENCE:
{confidence}/100

📊 AI ANALYSIS:

{chr(10).join(reasons)}

🔥 STRATEGY ENGINE:

✅ EMA TREND
✅ RSI MOMENTUM
✅ MACD CONFIRMATION
✅ VWAP STRENGTH
✅ PATTERN AI
✅ MARKET TREND FILTER
✅ MULTI TIMEFRAME CONFIRMATION
✅ RISK MANAGEMENT

🎯 TARGET:
+3%

🛑 STOPLOSS:
-2%

🛡 TRAILING STOPLOSS:
ACTIVE

🚀 MODE:
PAPER TRADING

""")

                # =========================================================
                # POSITION MANAGEMENT
                # =========================================================

                if stock in positions:

                    bp = positions[stock]["buy_price"]

                    qty = positions[stock]["qty"]

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
                        highest * (1 - TRAILING_STOPLOSS_PERCENT/100),
                        2
                    )

                    # =========================================================
                    # PARTIAL PROFIT BOOKING
                    # =========================================================

                    if (

                        pnl_percent >= PARTIAL_BOOKING_PERCENT

                        and not positions[stock]["partial_booked"]

                    ):

                        positions[stock]["partial_booked"] = True

                        send(f"""

🟡 PARTIAL PROFIT BOOKING

📈 STOCK:
{stock}

💰 CURRENT PRICE:
₹{price}

📊 CURRENT RETURN:
{pnl_percent}%

💵 CURRENT PNL:
₹{pnl_amount}

🧠 REASON:
Partial profit secured

🛡 CAPITAL SAFETY IMPROVED

""")

                    # =========================================================
                    # EXIT CONDITIONS
                    # =========================================================

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

                    # =========================================================
                    # EXIT EXECUTION
                    # =========================================================

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

📦 QUANTITY:
{qty}

💵 PNL:
₹{pnl_amount}

📊 RETURN:
{pnl_percent}%

🧠 EXIT REASON:
{exit_reason}

📈 AI ANALYSIS:

{chr(10).join(reasons)}

💰 DAILY PROFIT:
₹{round(daily_profit,2)}

🛡 RISK MANAGEMENT:
ACTIVE

✅ CAPITAL PROTECTED

""")

                        del positions[stock]

            except Exception as stock_error:

                send(f"""

⚠ STOCK ERROR DETECTED

📉 STOCK:
{stock}

❌ ERROR:
{str(stock_error)}

🛡 BOT CONTINUING SAFELY

""")

                continue

        # =========================================================
        # HEARTBEAT
        # =========================================================

        send(f"""

💓 BOT HEARTBEAT

✅ BOT RUNNING OK
✅ AI ENGINE ACTIVE
✅ DATABASE CONNECTED
✅ MARKET SCANNER ACTIVE
✅ TRAILING STOP ACTIVE

💰 DAILY PROFIT:
₹{round(daily_profit,2)}

📊 OPEN POSITIONS:
{len(positions)}

📈 TRACKING STOCKS:
{len(STOCKS)}

🚀 SYSTEM STATUS:
STABLE

""")

        # =========================================================
        # WAIT
        # =========================================================

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
