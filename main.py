import yfinance as yf
import time
import requests
import os

from db import *
from ai import *
from risk import *
from market import *
from strategy import *
from telegram_control import *
from broker import *

CAPITAL=200000

positions={}

daily_profit=0

STOCKS=[

"HDFCBANK.NS","ICICIBANK.NS","SBIN.NS",
"TCS.NS","INFY.NS","WIPRO.NS",
"RELIANCE.NS","TATASTEEL.NS","HINDZINC.NS",
"HINDCOPPER.NS","SUNPHARMA.NS","DRREDDY.NS",
"CIPLA.NS","COFORGE.NS","TRENT.NS"

]

init_db()

send("🚀 V30 ELITE PRO MAX STARTED")

while True:

    try:

        trend=market_trend()

        send(f"📊 Market Trend: {trend}")

        for stock in STOCKS:

            df=yf.download(

                stock,
                period="5d",
                interval="15m",
                progress=False

            )

            if len(df)<100:
                continue

            score,reasons=apply_strategy(df,weights)

            price=float(df["Close"].iloc[-1])

            confidence=min(score,100)

            qty=position_size(
                CAPITAL,
                confidence,
                price
            )

            # MARKET FILTER

            if trend=="BEARISH" and confidence<80:
                continue

            # BUY

            if confidence>=70 and stock not in positions:

                positions[stock]={

                    "buy_price":price,
                    "qty":qty

                }

                place_order(stock,"BUY",qty)

                send(f"""

🟢 AI BUY SIGNAL

📈 STOCK: {stock}

💰 ENTRY PRICE: ₹{round(price,2)}

📦 QTY: {qty}

🧠 CONFIDENCE: {confidence}/100

📊 AI ANALYSIS:

{chr(10).join(reasons)}

🔥 STRATEGY:
EMA + RSI + MACD + VWAP + Pattern AI

🛡 RISK MANAGEMENT ACTIVE

""")

            # EXIT

            if stock in positions:

                bp=positions[stock]["buy_price"]

                pnl=((price-bp)/bp)*100

                if pnl>=3 or pnl<=-2:

                    reason="Target Achieved"

                    if pnl<=-2:
                        reason="Stop Loss Hit"

                    send(f"""

🔴 POSITION EXIT

📉 STOCK: {stock}

💰 EXIT PRICE: ₹{round(price,2)}

📊 RETURN: {round(pnl,2)}%

🧠 EXIT REASON:
{reason}

📈 AI CONDITIONS:
{chr(10).join(reasons)}

🛡 CAPITAL PROTECTED

""")

                    del positions[stock]

        # HEARTBEAT

        send("💓 BOT RUNNING OK")

        time.sleep(1800)

    except Exception as e:

        send(f"⚠ ERROR: {str(e)}")

        time.sleep(60)
