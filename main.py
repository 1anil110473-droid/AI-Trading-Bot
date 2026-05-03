from db import init_db, save_trade, save_position, delete_position, load_positions
from db import load_weights, update_weights
import yfinance as yf
import pandas as pd
import time, os, requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ===== TELEGRAM SAFE =====
def send(msg):
    try:
        if TOKEN and CHAT_ID:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg},
                timeout=5
            )
        print(msg)
    except Exception as e:
        print("Telegram error:", e)

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

def safe(x):
    try:
        return float(x.values[0]) if hasattr(x,"values") else float(x)
    except:
        return 0.0

# ===== DATA SAFE =====
def get_df(stock, interval="5m"):
    for _ in range(3):
        try:
            df = yf.download(
                stock,
                period="2d",
                interval=interval,
                progress=False,
                threads=False
            )
            if df is None or df.empty or len(df) < 50:
                time.sleep(1)
                continue
            return df
        except Exception as e:
            print("DATA ERROR:", stock, e)
            time.sleep(1)
    return None

def indicators(df):
    df = df.copy()

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
    score += weights.get("EMA",25) if safe(row["EMA5"])>safe(row["EMA15"]) else -weights.get("EMA",25)
    score += weights.get("RSI",15) if safe(row["RSI"])>0 else -weights.get("RSI",15)
    score += weights.get("VWAP",20) if safe(row["Close"])>safe(row["VWAP"]) else -weights.get("VWAP",20)
    score += weights.get("MACD",25) if safe(row["MACD"])>safe(row["MACD_SIGNAL"]) else -weights.get("MACD",25)
    return score

def restore_state():
    for s, data in positions.items():
        df = get_df(s)
        if df is not None:
            df = indicators(df)
            if not df.empty:
                highest_price[s] = max(data["entry"], safe(df.iloc[-1]["Close"]))
        else:
            highest_price[s] = data["entry"]

        last_trade_time[s] = time.time() - 300

def run():
    global positions, weights

    send("🚀 BOT STARTED")
    init_db()

    weights = load_weights()
    send(f"🧠 AI Weights: {weights}")

    positions = load_positions()
    restore_state()

    last_heartbeat = time.time()

    while True:
        loop_start = time.time()

        try:
            nifty_df = get_df("^NSEI")
            nifty_trend = True

            if nifty_df is not None:
                nifty_df = indicators(nifty_df)
                if not nifty_df.empty:
                    last_nifty = nifty_df.iloc[-1]
                    nifty_trend = safe(last_nifty["EMA5"]) > safe(last_nifty["EMA15"])

            for s in STOCKS:
                try:
                    df5 = get_df(s, "5m")
                    df15 = get_df(s, "15m")

                    if df5 is None or df15 is None:
                        continue

                    df5 = indicators(df5)
                    df15 = indicators(df15)

                    if df5.empty or df15.empty:
                        continue

                    last5 = df5.iloc[-1]
                    last15 = df15.iloc[-1]

                    score = ai_score(last5)
                    price = safe(last5["Close"])
                    volume = safe(last5["Volume"])
                    vol_avg = safe(last5["VOL_AVG"])

                    pos = positions.get(s)

                    trend_ok = safe(last5["EMA5"]) > safe(last5["EMA15"])
                    volume_ok = volume > vol_avg
                    mtf_ok = safe(last15["EMA5"]) > safe(last15["EMA15"])

                    now = time.time()
                    last_time = last_trade_time.get(s, 0)

                    if score >= 60 and not pos and trend_ok and volume_ok and mtf_ok and nifty_trend and (now-last_time>300):
                        positions[s] = {"entry": price}
                        save_position(s, price)
                        highest_price[s] = price
                        last_trade_time[s] = now
                        send(f"🟢 BUY {s} @ {price}")

                    if pos:
                        highest_price[s] = max(highest_price.get(s, price), price)

                        trail_sl = highest_price[s] * 0.98
                        pnl = price - pos["entry"]

                        if pnl > 2:
                            trail_sl = highest_price[s] * 0.99

                        if price < trail_sl or score <= -60:
                            save_trade(s, pos["entry"], price, pnl)
                            delete_position(s)
                            update_weights(weights, pnl)

                            send(f"🔒 EXIT {s} ₹{round(pnl,2)}")

                            del positions[s]
                            if s in highest_price:
                                del highest_price[s]

                except Exception as e:
                    print("STOCK ERROR:", s, e)

            # HEARTBEAT 3 HOURS
            if time.time() - last_heartbeat > 10800:
                send("🤖 BOT RUNNING OK")
                last_heartbeat = time.time()

            # LOOP STUCK ALERT
            if time.time() - loop_start > 300:
                send("⚠️ LOOP SLOW")

            time.sleep(60)

        except Exception as e:
            send(f"⚠️ ERROR {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()
