import yfinance as yf
import time
import traceback

from db import init_db
from ai import weights
from risk import position_size
from market import market_trend
from strategy import apply_strategy
from telegram_control import send
from broker import place_order

# ==========================================
# CAPITAL CONFIGURATION
# ==========================================

CAPITAL = 200000

DAILY_TARGET = 1000

# ==========================================
# GLOBAL VARIABLES
# ==========================================

positions = {}

daily_profit = 0

# ==========================================
# STOCK LIST
# ==========================================

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

# ==========================================
# DATABASE INITIALIZATION
# ==========================================

init_db()

# ==========================================
# START MESSAGE
# ==========================================

send("""

🚀 V30 ELITE PRO MAX STARTED

✅ AI ENGINE ACTIVE
✅ MARKET SCANNER ACTIVE
✅ RISK MANAGEMENT ACTIVE
✅ HEARTBEAT ACTIVE
✅ PAPER TRADING MODE ACTIVE

💰 CAPITAL: ₹200000
🎯 DAILY TARGET: ₹1000

""")

# ==========================================
# MAIN LOOP
# ==========================================

while True:

    try:

        # ==========================================
        # DAILY TARGET CHECK
        # ==========================================

        if daily_profit >= DAILY_TARGET:

            send(f"""

🎯 DAILY TARGET ACHIEVED

💰 TOTAL DAILY PROFIT:
₹{round(daily_profit, 2)}

🛑 NEW TRADES STOPPED

✅ CAPITAL PROTECTED
✅ OVERTRADING PREVENTED

🚀 BOT WAITING FOR NEXT SESSION

""")

            time.sleep(1800)
            continue

        # ==========================================
        # MARKET TREND
        # ==========================================

        trend = market_trend()

        send(f"""

📊 MARKET TREND UPDATE

📈 CURRENT TREND:
{trend}

🧠 AI MARKET FILTER ACTIVE

""")

        # ==========================================
        # STOCK LOOP
        # ==========================================

        for stock in STOCKS:

            try:

                # ==========================================
                # DOWNLOAD MARKET DATA
                # ==========================================

                df = yf.download(

                    stock,
                    period="5d",
                    interval="15m",
                    auto_adjust=True,
                    progress=False

                )

                # ==========================================
                # SAFETY CHECK
                # ==========================================

                if df.empty or len(df) < 100:
                    continue

                # ==========================================
                # APPLY AI STRATEGY
                # ==========================================

                score, reasons = apply_strategy(df, weights)

                # ==========================================
                # CURRENT PRICE
                # ==========================================

                price = round(
                    float(df["Close"].iloc[-1]),
                    2
                )

                # ==========================================
                # AI CONFIDENCE
                # ==========================================

                confidence = min(score, 100)

                # ==========================================
                # SMART POSITION SIZE
                # ==========================================

                qty = position_size(
                    CAPITAL,
                    confidence,
                    price
                )

                # ==========================================
                # MARKET FILTER
                # ==========================================

                if trend == "BEARISH" and confidence < 80:
                    continue

                # ==========================================
                # BUY LOGIC
                # ==========================================

                if confidence >= 70 and stock not in positions:

                    positions[stock] = {

                        "buy_price": price,
                        "qty": qty,
                        "highest_price": price

                    }

                    # ==========================================
                    # PLACE ORDER
                    # ==========================================

                    place_order(stock, "BUY", qty)

                    # ==========================================
                    # TELEGRAM BUY ALERT
                    # ==========================================

                    send(f"""

🟢 AI BUY SIGNAL

📈 STOCK:
{stock}

💰 ENTRY PRICE:
₹{price}

📦 QUANTITY:
{qty}

💵 INVESTMENT VALUE:
₹{round(price * qty, 2)}

🧠 AI CONFIDENCE:
{confidence}/100

📊 AI ANALYSIS:

{chr(10).join(reasons)}

🔥 STRATEGY ENGINE:

✅ EMA TREND ANALYSIS
✅ RSI MOMENTUM ANALYSIS
✅ MACD CONFIRMATION
✅ VWAP STRENGTH
✅ PATTERN AI DETECTION
✅ MARKET TREND FILTER
✅ SMART RISK MANAGEMENT

🎯 TARGET:
+3%

🛑 STOP LOSS:
-2%

🛡 TRAILING PROTECTION:
ACTIVE

🚀 BOT MODE:
PAPER TRADING

""")

                # ==========================================
                # POSITION MANAGEMENT
                # ==========================================

                if stock in positions:

                    buy_price = positions[stock]["buy_price"]

                    qty = positions[stock]["qty"]

                    # ==========================================
                    # HIGHEST PRICE TRACKER
                    # ==========================================

                    if price > positions[stock]["highest_price"]:

                        positions[stock]["highest_price"] = price

                    highest_price = positions[stock]["highest_price"]

                    # ==========================================
                    # PNL CALCULATION
                    # ==========================================

                    pnl_percent = round(
                        ((price - buy_price) / buy_price) * 100,
                        2
                    )

                    pnl_amount = round(
                        ((price - buy_price) * qty),
                        2
                    )

                    # ==========================================
                    # TRAILING STOP LOSS
                    # ==========================================

                    trailing_sl = round(
                        highest_price * 0.985,
                        2
                    )

                    # ==========================================
                    # EXIT CONDITIONS
                    # ==========================================

                    exit_reason = None

                    # TARGET EXIT

                    if pnl_percent >= 3:

                        exit_reason = "TARGET ACHIEVED"

                    # STOP LOSS EXIT

                    elif pnl_percent <= -2:

                        exit_reason = "STOP LOSS HIT"

                    # TRAILING STOP LOSS

                    elif price <= trailing_sl and pnl_percent > 0:

                        exit_reason = "TRAILING STOP LOSS HIT"

                    # ==========================================
                    # EXIT EXECUTION
                    # ==========================================

                    if exit_reason:

                        daily_profit += pnl_amount

                        send(f"""

🔴 POSITION EXIT

📉 STOCK:
{stock}

💰 EXIT PRICE:
₹{price}

📦 QUANTITY:
{qty}

💵 PNL AMOUNT:
₹{pnl_amount}

📊 RETURN:
{pnl_percent}%

🧠 EXIT REASON:
{exit_reason}

📈 AI MARKET CONDITIONS:

{chr(10).join(reasons)}

🛡 RISK MANAGEMENT:
ACTIVE

💰 CURRENT DAILY PROFIT:
₹{round(daily_profit,2)}

🔥 EXIT ANALYSIS COMPLETE

✅ CAPITAL PROTECTED

""")

                        del positions[stock]

            # ==========================================
            # SINGLE STOCK ERROR HANDLING
            # ==========================================

            except Exception as stock_error:

                send(f"""

⚠ STOCK ERROR DETECTED

📉 STOCK:
{stock}

❌ ERROR MESSAGE:
{str(stock_error)}

🛡 BOT CONTINUING SAFELY

""")

                continue

        # ==========================================
        # HEARTBEAT MESSAGE
        # ==========================================

        send(f"""

💓 BOT HEARTBEAT

✅ BOT RUNNING OK
✅ AI ENGINE ACTIVE
✅ DATABASE CONNECTED
✅ MARKET SCANNER ACTIVE

💰 DAILY PROFIT:
₹{round(daily_profit,2)}

📊 TRACKING STOCKS:
{len(STOCKS)}

🚀 SYSTEM STATUS:
STABLE

""")

        # ==========================================
        # WAIT TIME
        # ==========================================

        time.sleep(1800)

    # ==========================================
    # MAIN LOOP ERROR HANDLER
    # ==========================================

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
