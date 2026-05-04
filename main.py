import os, time, requests
import numpy as np
import yfinance as yf

from db import *
from model import create_model, prepare_data
from sentiment import get_sentiment

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CAPITAL = 200000
equity = CAPITAL
peak = CAPITAL

positions = {}

STOCKS = [
"HDFCBANK.NS","ICICIBANK.NS","SBIN.NS",
"TCS.NS","INFY.NS","WIPRO.NS",
"RELIANCE.NS","TATASTEEL.NS","HINDZINC.NS",
"HINDCOPPER.NS","SUNPHARMA.NS","DRREDDY.NS",
"CIPLA.NS","COFORGE.NS","TRENT.NS"
]

model = create_model()

def send(msg):
    try:
        if TOKEN:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass
    print(msg)

# ===== MULTI TF DATA =====
def get_data(stock, interval):
    df = yf.download(stock, period="3mo", interval=interval, progress=False)
    if df is None or df.empty:
        return None
    return df["Close"].values

# ===== LSTM PREDICT =====
def predict(series):
    X, y = prepare_data(series)
    if len(X) < 20:
        return 0

    model.fit(X, y, epochs=1, verbose=0)
    pred = model.predict(X[-1].reshape(1,10,1))
    return float(pred[0][0])

def run():
    global equity, peak

    init_db()
    send("🚀 V34 QUANT BOT STARTED")

    while True:
        try:
            for s in STOCKS:

                # ===== MULTI TIMEFRAME =====
                d1 = get_data(s,"1h")
                d2 = get_data(s,"15m")
                d3 = get_data(s,"5m")

                if d1 is None or d2 is None or d3 is None:
                    continue

                price = d3[-1]

                # ===== ML PREDICTIONS =====
                p1 = predict(d1)
                p2 = predict(d2)
                p3 = predict(d3)

                # ===== COMBINED SIGNAL =====
                ml_signal = ((p1-price)/price + (p2-price)/price + (p3-price)/price) / 3

                # ===== NEWS SENTIMENT =====
                sentiment = get_sentiment(s)

                # ===== RL =====
                rl = get_avg_reward()

                # ===== FINAL CONFIDENCE =====
                confidence = ml_signal + sentiment + rl

                pos = positions.get(s)

                qty = max(1, int((equity*0.1)/price))

                # ===== ENTRY =====
                if confidence > 0.02 and not pos:
                    positions[s] = {"entry":price,"qty":qty,"type":"LONG"}
                    save_position(s, price, qty, "LONG")
                    send(f"🟢 BUY {s} @ {price}")

                elif confidence < -0.02 and not pos:
                    positions[s] = {"entry":price,"qty":qty,"type":"SHORT"}
                    save_position(s, price, qty, "SHORT")
                    send(f"🔴 SHORT {s} @ {price}")

                # ===== EXIT =====
                if pos:
                    pnl = (price - pos["entry"]) * pos["qty"]
                    if pos["type"] == "SHORT":
                        pnl = -pnl

                    save_reward(pnl)

                    equity += pnl
                    peak = max(peak, equity)

                    dd = (peak - equity) / peak

                    if pnl > 500 or pnl < -500 or dd > 0.25:
                        save_trade(s, pos["entry"], price, pnl)
                        delete_position(s)

                        send(f"🔒 EXIT {s} ₹{round(pnl,2)} | Eq:{round(equity)}")

                        del positions[s]

            time.sleep(60)

        except Exception as e:
            send(f"ERROR {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()
