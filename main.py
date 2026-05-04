from db import *
import yfinance as yf
import pandas as pd
import time, os, requests
from datetime import datetime, timedelta

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CAPITAL = 100000
RISK_PER_TRADE = 0.02

positions = {}
last_trade_time = {}
highest_price = {}
weights = {}

STOCKS = [
"HDFCBANK.NS","ICICIBANK.NS","SBIN.NS",
"TCS.NS","INFY.NS","WIPRO.NS",
"RELIANCE.NS","TATASTEEL.NS","HINDZINC.NS",
"HINDCOPPER.NS","SUNPHARMA.NS","DRREDDY.NS",
"CIPLA.NS","COFORGE.NS","TRENT.NS"
]

def send(msg):
    try:
        if TOKEN and CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
        print(msg)
    except:
        pass

def safe(x):
    try:
        return float(x.values[0]) if hasattr(x,"values") else float(x)
    except:
        return 0.0

def get_ist():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def market_open():
    now = get_ist()
    if now.weekday() >= 5:
        return False
    return (9 <= now.hour <= 15)

def get_df(stock, interval="5m"):
    for _ in range(3):
        try:
            df = yf.download(stock, period="5d", interval=interval, progress=False)
            if df is not None and not df.empty and len(df) > 50:
                return df
        except:
            pass
        time.sleep(2)
    return None

def indicators(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df["EMA5"] = df["Close"].ewm(span=5).mean()
    df["EMA15"] = df["Close"].ewm(span=15).mean()
    df["RET"] = df["Close"].pct_change()
    df["RSI"] = df["RET"].rolling(14).mean()*100
    df["VWAP"] = (df["Close"]*df["Volume"]).cumsum()/df["Volume"].cumsum()
    df["VOL_AVG"] = df["Volume"].rolling(20).mean()
    df["EMA12"] = df["Close"].ewm(span=12).mean()
    df["EMA26"] = df["Close"].ewm(span=26).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9).mean()
    return df.dropna()

def ai_score(row):
    score = 0
    score += weights.get("EMA",25) if safe(row["EMA5"])>safe(row["EMA15"]) else -25
    score += weights.get("RSI",15) if safe(row["RSI"])>0 else -15
    score += weights.get("VWAP",20) if safe(row["Close"])>safe(row["VWAP"]) else -20
    score += weights.get("MACD",25) if safe(row["MACD"])>safe(row["MACD_SIGNAL"]) else -25
    return score

def build_pattern(row):
    trend = "UP" if safe(row["EMA5"])>safe(row["EMA15"]) else "DOWN"
    rsi = safe(row["RSI"])
    zone = "LOW" if rsi<30 else "HIGH" if rsi>70 else "MID"
    macd = "UP" if safe(row["MACD"])>safe(row["MACD_SIGNAL"]) else "DOWN"
    return f"{trend}_{zone}_{macd}"

def position_size(price):
    return max(1, int((CAPITAL*RISK_PER_TRADE)/price))

def get_mode(nifty):
    gap = abs(safe(nifty["EMA5"]) - safe(nifty["EMA15"]))
    return "AGGRESSIVE" if gap > 15 else "SAFE"

def run():
    global weights, positions

    send("🚀 V20 DUAL MODE BOT STARTED")
    init_db()

    weights = load_weights()
    positions = load_positions()

    while True:
        try:
            if not market_open():
                time.sleep(300)
                continue

            nifty_df = get_df("^NSEI")
            if nifty_df is None: continue
            nifty_df = indicators(nifty_df)
            nifty = nifty_df.iloc[-1]

            mode = get_mode(nifty)

            for s in STOCKS:
                df5 = get_df(s,"5m")
                if df5 is None: continue

                df5 = indicators(df5)
                row = df5.iloc[-1]

                score = ai_score(row)
                price = safe(row["Close"])
                pos = positions.get(s)

                pattern = build_pattern(row)
                pscore = get_pattern_score(pattern) or 0.5

                # ===== MODE SETTINGS =====
                if mode == "AGGRESSIVE":
                    entry_threshold = 50
                    cooldown = 120
                else:
                    entry_threshold = 60
                    cooldown = 300

                now = time.time()

                # ENTRY
                if score >= entry_threshold and not pos and pscore>=0.4:
                    qty = position_size(price)
                    positions[s] = {"entry":price,"qty":qty,"time":now}
                    save_position(s,price)
                    highest_price[s]=price
                    send(f"🟢 {mode} BUY {s} @ {price}")

                # EXIT
                if pos:
                    highest_price[s] = max(highest_price.get(s,price),price)
                    pnl = (price-pos["entry"])*pos["qty"]
                    trail = highest_price[s]*0.985

                    if price < trail or score <= -50:
                        save_trade(s,pos["entry"],price,pnl)
                        delete_position(s)
                        update_weights(weights,pnl)
                        save_pattern(pattern,pnl)
                        send(f"🔒 EXIT {s} ₹{round(pnl,2)}")
                        del positions[s]

            time.sleep(60)

        except Exception as e:
            send(f"ERROR {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()
