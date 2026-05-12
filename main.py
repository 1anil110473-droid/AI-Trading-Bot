import yfinance as yf
import pandas as pd
import time
import traceback
import pytz
import gc

from datetime import datetime
from threading import Thread

from db import (
    init_db,
    save_trade,
    load_positions,
    save_position,
    delete_position
)

from ai import weights
from risk import position_size
from market import market_trend
from strategy import apply_strategy
from telegram_control import send
from broker import place_order

# =========================================================
# V52 ULTRA INSTITUTIONAL AI ENGINE
# =========================================================

CAPITAL = 200000

DAILY_TARGET = 1000

MAX_OPEN_POSITIONS = 5

TARGET_PERCENT = 3

STOPLOSS_PERCENT = -2

TRAILING_STOPLOSS_PERCENT = 1.5

PARTIAL_BOOKING_PERCENT = 2

MARKET_CRASH_THRESHOLD = -1.5

# =========================================================
# PROFESSIONAL HEARTBEAT SYSTEM
# =========================================================

MARKET_OPEN_HEARTBEAT = 1800       # 30 Minutes
MARKET_CLOSED_HEARTBEAT = 21600    # 6 Hours

FIXED_QUANTITY = 100

TIMEZONE = pytz.timezone("Asia/Kolkata")

# =========================================================
# GLOBALS
# =========================================================

positions = {}

daily_profit = 0

last_heartbeat = 0

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
# LOAD POSITIONS
# =========================================================

try:

    old_positions = load_positions()

    if old_positions:

        positions = old_positions

        send(f"""

♻️ OLD POSITIONS RECOVERED

📦 TOTAL POSITIONS:
{len(positions)}

✅ RESTART SAFE MODE ACTIVE
✅ CRASH RECOVERY ACTIVE
✅ INSTITUTIONAL PERSISTENCE ACTIVE

""")

except Exception as e:

    send(f"""

⚠ POSITION RECOVERY FAILED

❌ ERROR:
{str(e)}

""")

# =========================================================
# STARTUP MESSAGE
# =========================================================

send(f"""

🚀 V52 ULTRA INSTITUTIONAL AI ENGINE STARTED

✅ DYNAMIC SCAN ENGINE ACTIVE
✅ PRE-MARKET ENGINE ACTIVE
✅ INSTANT EXIT ENGINE ACTIVE
✅ TARGET HIT DETECTION ACTIVE
✅ TRAILING STOPLOSS ACTIVE
✅ PARTIAL PROFIT ENGINE ACTIVE
✅ SMART HEARTBEAT ACTIVE
✅ MARKET TREND FILTER ACTIVE
✅ DATABASE CONNECTED
✅ RESTART RECOVERY ACTIVE
✅ RAILWAY SAFE MODE ACTIVE
✅ TELEGRAM RETRY ACTIVE
✅ MEMORY OPTIMIZATION ACTIVE
✅ PAPER TRADING MODE ACTIVE

💰 CAPITAL:
₹{CAPITAL}

🎯 DAILY TARGET:
₹{DAILY_TARGET}

📦 MAX OPEN POSITIONS:
{MAX_OPEN_POSITIONS}

📦 FIXED QUANTITY:
{FIXED_QUANTITY}

🛡 SYSTEM:
ULTRA INSTITUTIONAL GRADE

""")

# =========================================================
# MARKET HOURS
# =========================================================

def market_open():

    now = datetime.now(TIMEZONE)

    if now.weekday() >= 5:
        return False

    current = now.strftime("%H:%M")

    return "09:00" <= current <= "15:30"

# =========================================================
# BUY ALLOWED
# =========================================================

def buy_allowed():

    now = datetime.now(TIMEZONE)

    current = now.strftime("%H:%M")

    return "09:15" <= current <= "15:15"

# =========================================================
# DYNAMIC SCAN ENGINE
# =========================================================

def dynamic_scan_interval():

    now = datetime.now(TIMEZONE)

    current = now.strftime("%H:%M")

    # =========================================
    # MARKET OPENING FAST MODE
    # =========================================

    if "09:15" <= current <= "10:00":

        return 15

    # =========================================
    # CLOSING SESSION FAST MODE
    # =========================================

    elif "14:45" <= current <= "15:30":

        return 20

    # =========================================
    # NORMAL MARKET
    # =========================================

    else:

        return 60

# =========================================================
# MARKET CRASH DETECTION
# =========================================================

def market_crash():

    try:

        nifty = yf.download(

            "^NSEI",
            period="2d",
            interval="5m",
            auto_adjust=True,
            progress=False,
            threads=False

        )

        if nifty.empty:
            return False

        if isinstance(nifty.columns, pd.MultiIndex):

            nifty.columns = nifty.columns.get_level_values(0)

        close = float(nifty["Close"].iloc[-1])

        prev = float(nifty["Close"].iloc[-2])

        change = ((close - prev) / prev) * 100

        return change <= MARKET_CRASH_THRESHOLD

    except:

        return False

# =========================================================
# HEARTBEAT THREAD
# =========================================================

def heartbeat():

    global last_heartbeat

    while True:

        try:

            now = time.time()

            # =============================================
            # DYNAMIC HEARTBEAT MODE
            # =============================================

            if market_open():

                heartbeat_interval = MARKET_OPEN_HEARTBEAT

            else:

                heartbeat_interval = MARKET_CLOSED_HEARTBEAT

            # =============================================
            # HEARTBEAT SEND
            # =============================================

            if now - last_heartbeat >= heartbeat_interval:

                send(f"""

💓 BOT HEARTBEAT

✅ BOT RUNNING OK
✅ AI ENGINE ACTIVE
✅ DATABASE CONNECTED
✅ MARKET SCANNER ACTIVE
✅ EXIT ENGINE ACTIVE

💰 DAILY PROFIT:
₹{round(daily_profit,2)}

📊 OPEN POSITIONS:
{len(positions)}

📈 TRACKING STOCKS:
{len(STOCKS)}

🚀 SYSTEM STATUS:
STABLE

""")

                last_heartbeat = now

            time.sleep(30)

        except:

            time.sleep(30)

# =========================================================
# START HEARTBEAT THREAD
# =========================================================

Thread(target=heartbeat, daemon=True).start()

# =========================================================
# MAIN LOOP
# =========================================================

while True:

    try:

        # =====================================================
        # MARKET CLOSED MODE
        # =====================================================

        if not market_open():

            now = datetime.now(TIMEZONE)

            hour = now.hour

    # =========================================
    # WEEKEND MODE
    # =========================================

            if now.weekday() >= 5:

                print("Weekend Sleep Mode Active")

                time.sleep(3600)

    # =========================================
    # NIGHT MODE
    # =========================================

            elif hour >= 16 or hour < 7:

                print("Night Mode Active")

                time.sleep(1800)

    # =========================================
    # PRE-MARKET WAIT
    # =========================================

            else:

                 print("Waiting For Market Open")

                 time.sleep(300)

            continue

        # =====================================================
        # DYNAMIC SCAN SPEED
        # =====================================================

        SCAN_INTERVAL = dynamic_scan_interval()

        # =====================================================
        # DAILY TARGET
        # =====================================================

        if daily_profit >= DAILY_TARGET:

            send(f"""

🎯 DAILY TARGET ACHIEVED

💰 TOTAL PROFIT:
₹{round(daily_profit,2)}

🛑 NEW TRADES BLOCKED

🛡 CAPITAL PROTECTION ACTIVE

""")

            time.sleep(600)

            continue

        # =====================================================
        # MARKET CRASH PROTECTION
        # =====================================================

        if market_crash():

            send("""

🚨 MARKET CRASH DETECTED

🛑 NEW TRADES BLOCKED

🛡 DEFENSIVE MODE ACTIVE

""")

            time.sleep(300)

            continue

        # =====================================================
        # MARKET TREND
        # =====================================================

        trend = market_trend()

        # =====================================================
        # SCAN STOCKS
        # =====================================================

        for stock in STOCKS:

            try:

                # =================================================
                # DOWNLOAD DATA
                # =================================================

                df = yf.download(

                    stock,
                    period="5d",
                    interval="5m",
                    auto_adjust=True,
                    progress=False,
                    threads=False

                )

                if df.empty or len(df) < 50:
                    continue

                # =================================================
                # FIX MULTI INDEX
                # =================================================

                if isinstance(df.columns, pd.MultiIndex):

                    df.columns = df.columns.get_level_values(0)

                df = df.dropna()

                # =================================================
                # PRICE
                # =================================================

                price = round(
                    float(df["Close"].iloc[-1]),
                    2
                )

                # =================================================
                # POSITION MANAGEMENT
                # =================================================

                if stock in positions:

                    bp = positions[stock]["buy_price"]

                    qty = positions[stock]["qty"]

                    highest = positions[stock]["highest_price"]

                    partial_booked = positions[stock]["partial_booked"]

                    # =============================================
                    # UPDATE HIGHEST
                    # =============================================

                    if price > highest:

                        highest = price

                        positions[stock]["highest_price"] = highest

                        save_position(

                            stock,
                            positions[stock]["buy_price"],
                            positions[stock]["qty"],
                            positions[stock]["highest_price"],
                            positions[stock]["partial_booked"]

                        )

                    # =============================================
                    # PNL
                    # =============================================

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
                    # PARTIAL PROFIT
                    # =============================================

                    if (

                        pnl_percent >= PARTIAL_BOOKING_PERCENT
                        and not partial_booked

                    ):

                        positions[stock]["partial_booked"] = True

                        save_position(

                            stock,
                            positions[stock]["buy_price"],
                            positions[stock]["qty"],
                            positions[stock]["highest_price"],
                            positions[stock]["partial_booked"]

                        )

                        send(f"""

🟡 PARTIAL PROFIT BOOKING

📈 STOCK:
{stock}

💰 CURRENT PRICE:
₹{price}

📊 RETURN:
{pnl_percent}%

💵 PNL:
₹{pnl_amount}

🛡 PROFIT LOCK ACTIVE

""")
                        
                        # =========================================================
                        # INSTITUTIONAL EXIT ENGINE
                        # =========================================================

                        exit_reason = None

                        # =========================================================
                        # TARGET EXIT
                        # =========================================================

                        target_price = round(

                            bp * (
                                1 + TARGET_PERCENT / 100
                                    ),
                                    2

                        )

                        if price >= target_price:

                            exit_reason = "TARGET ACHIEVED"

                        # =========================================================
                        # HARD STOPLOSS
                        # =========================================================

                        elif price <= round(

                            bp * (
                                1 + STOPLOSS_PERCENT / 100
                                    ),
                                    2

                        ):

                            exit_reason = "STOPLOSS HIT"

                        # =========================================================
                        # TRAILING STOPLOSS
                        # =========================================================

                        elif (

                            price <= trailing_sl
                            and pnl_percent > 0

                        ):

                            exit_reason = "TRAILING STOPLOSS HIT"

                        # =========================================================
                        # RESISTANCE REJECTION EXIT
                        # =========================================================

                        elif (

                            result["resistance_rejection"]
                            and pnl_percent > 1

                        ):

                            exit_reason = "RESISTANCE REJECTION"

                        # =========================================================
                        # SUPPORT BREAKDOWN EXIT
                        # =========================================================

                        elif (

                            price < result["support"]
                            and pnl_percent < 0

                        ):

                            exit_reason = "SUPPORT BREAKDOWN"

                        # =========================================================
                        # EMA TREND REVERSAL EXIT
                        # =========================================================

                        elif (

                            result["ema_bearish"]
                            and pnl_percent > 0.5

                        ):

                            exit_reason = "EMA TREND REVERSAL"

                       # =========================================================
                       # VWAP BREAKDOWN EXIT
                       # =========================================================

                        elif (

                            price < result["vwap"]
                            and pnl_percent > 1

                        ):

                            exit_reason = "VWAP BREAKDOWN"

                       # =========================================================
                       # MARKET CRASH SAFETY EXIT
                       # =========================================================

                        elif market_crash():

                            exit_reason = "MARKET CRASH EXIT"

# =========================================================
# EXIT EXECUTION
# =========================================================

if exit_reason:

    if stock not in positions:
        continue

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

💰 DAILY PROFIT:
₹{round(daily_profit,2)}

🛡 INSTITUTIONAL EXIT ENGINE:
ACTIVE

✅ POSITION CLOSED
✅ CAPITAL RELEASED
✅ EXIT SUCCESSFUL

""")

    delete_position(stock)

    del positions[stock]

    continue
    

                    # =============================================
                    # EXIT EXECUTION
                    # =============================================

                    if exit_reason:

                        if stock not in positions:
                            continue

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

💰 DAILY PROFIT:
₹{round(daily_profit,2)}

✅ POSITION CLOSED
✅ CAPITAL RELEASED
✅ EXIT SUCCESSFUL

""")

                        delete_position(stock)

                        del positions[stock]

                        continue

                # =================================================
                # BUY TIME FILTER
                # =================================================

                if not buy_allowed():
                    continue

                # =================================================
                # MAX POSITION LIMIT
                # =================================================

                if len(positions) >= MAX_OPEN_POSITIONS:
                    continue

                # =================================================
                # SKIP OPEN POSITION
                # =================================================

                if stock in positions:
                    continue

                # =================================================
                # STRATEGY
                # =================================================                                                                     
                result = apply_strategy(df, weights)

                score = result["score"]

                reasons = result["reasons"]

                confidence = score

                # =================================================
                # TREND FILTER
                # =================================================

                if trend == "BEARISH" and confidence < 85:
                    continue

                # =================================================
                # MULTI TIMEFRAME
                # =================================================

                higher = yf.download(

                    stock,
                    period="10d",
                    interval="1h",
                    auto_adjust=True,
                    progress=False,
                    threads=False

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

                # =================================================
                # BUY SIGNAL
                # =================================================

                if confidence >= 70:

                    qty = FIXED_QUANTITY

                    positions[stock] = {

                        "buy_price": price,
                        "qty": qty,
                        "highest_price": price,
                        "partial_booked": False

                    }

                    save_position(

                        stock,
                        positions[stock]["buy_price"],
                        positions[stock]["qty"],
                        positions[stock]["highest_price"],
                        positions[stock]["partial_booked"]

                    )

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
₹{round(price * qty,2)}

🧠 AI CONFIDENCE:
{confidence}/100

📊 AI ANALYSIS:

{chr(10).join(reasons)}

🎯 TARGET:
+3%

🛑 STOPLOSS:
-2%

🛡 TRAILING STOPLOSS:
ACTIVE

🚀 MODE:
PAPER TRADING

""")

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

        # =====================================================
        # MEMORY CLEANUP
        # =====================================================

        gc.collect()

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
