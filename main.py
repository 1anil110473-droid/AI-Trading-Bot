from db import init_db, save_trade, save_position, delete_position, load_positions
from db import load_weights, update_weights, get_trades
from db import save_pattern, get_pattern_score   # 🔥 NEW
import yfinance as yf
import pandas as pd
import time, os, requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

positions = {}
last_trade_time = {}
highest_price = {}
weights = {}
last_pnl = 0

STOCKS = [
"HDFCBANK.NS","ICICIBANK.NS","SBIN.NS",
"TCS.NS","INFY.NS","WIPRO.NS",
"RELIANCE.NS","TATASTEEL.NS","HINDZINC.NS",
"HINDCOPPER.NS","SUNPHARMA.NS","DRREDDY.NS",
"CIPLA.NS","COFORGE.NS","TRENT.NS"
]

# ===== TELEGRAM =====
def send(msg):
    try:
        if TOKEN:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg}
            )
        print(msg)
    except:
        print("Telegram error")

# ===== SAFE =====
def safe(x):
    try:
        return float(x.values[0]) if hasattr(x,"values") else float(x)
    except:
        return 0.0

# ===== DATA =====
def get_df(stock, interval="5m"):
    try:
        df = yf.download(stock, period="2d", interval=interval, progress=False)
        if df is None or df.empty or len(df) < 50:
            return None
        return df
    except:
        return None

# ===== INDICATORS =====
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

# ===== AI SCORE =====
def ai_score(row):
    score = 0
    score += weights.get("EMA",25) if safe(row["EMA5"])>safe(row["EMA15"]) else -weights.get("EMA",25)
    score += weights.get("RSI",15) if safe(row["RSI"])>0 else -weights.get("RSI",15)
    score += weights.get("VWAP",20) if safe(row["Close"])>safe(row["VWAP"]) else -weights.get("VWAP",20)
    score += weights.get("MACD",25) if safe(row["MACD"])>safe(row["MACD_SIGNAL"]) else -weights.get("MACD",25)
    return score

# ===== PATTERN BUILDER =====
def build_pattern(row):
    trend = "UP" if safe(row["EMA5"]) > safe(row["EMA15"]) else "DOWN"

    rsi = safe(row["RSI"])
    if rsi < 30:
        rsi_zone = "LOW"
    elif rsi > 70:
        rsi_zone = "HIGH"
    else:
        rsi_zone = "MID"

    macd = "UP" if safe(row["MACD"]) > safe(row["MACD_SIGNAL"]) else "DOWN"

    return f"{trend}_{rsi_zone}_{macd}"

# ===== WIN RATE =====
def get_winrate():
    trades = get_trades()
    total = len(trades)
    wins = len([t for t in trades if t[3] > 0])
    return round((wins/total)*100,1) if total else 0

# ===== RESTORE =====
def restore():
    for s, data in positions.items():
        highest_price[s] = data["entry"]
        last_trade_time[s] = time.time() - 300

# ===== BOT =====
def run():
    global positions, weights, last_pnl

    send("🚀 V18 AI PATTERN BOT STARTED")
    init_db()

    weights = load_weights()
    send(f"🧠 AI Weights: {weights}")

    positions = load_positions()
    restore()

    last_heartbeat = time.time()

    while True:
        try:
            # ===== NIFTY =====
            nifty_df = get_df("^NSEI")
            nifty_trend = True

            if nifty_df is not None:
                nifty_df = indicators(nifty_df)
                if not nifty_df.empty:
                    last_nifty = nifty_df.iloc[-1]
                    nifty_trend = safe(last_nifty["EMA5"]) > safe(last_nifty["EMA15"])

            for s in STOCKS:
                try:
                    df5 = get_df(s,"5m")
                    df15 = get_df(s,"15m")

                    if df5 is None or df15 is None:
                        continue

                    df5 = indicators(df5)
                    df15 = indicators(df15)

                    if df5.empty or df15.empty:
                        continue

                    row = df5.iloc[-1]
                    row15 = df15.iloc[-1]

                    score = ai_score(row)
                    price = safe(row["Close"])
                    volume = safe(row["Volume"])
                    vol_avg = safe(row["VOL_AVG"])

                    pos = positions.get(s)

                    trend_ok = safe(row["EMA5"]) > safe(row["EMA15"])
                    mtf_ok = safe(row15["EMA5"]) > safe(row15["EMA15"])
                    volume_ok = volume > (1.2 * vol_avg)

                    # 🔥 PATTERN
                    pattern = build_pattern(row)
                    pattern_score = get_pattern_score(pattern)
                    pattern_ok = pattern_score >= 0.5

                    # 🔥 dynamic threshold
                    entry_threshold = 55
                    if trend_ok and mtf_ok and nifty_trend:
                        entry_threshold = 50

                    now = time.time()
                    last_time = last_trade_time.get(s,0)

                    # ===== ENTRY =====
                    if (score >= entry_threshold and pattern_ok and not pos and
                        trend_ok and mtf_ok and volume_ok and nifty_trend and
                        (now-last_time>300)):

                        positions[s] = {"entry": price, "time": now}
                        save_position(s, price)

                        highest_price[s] = price
                        last_trade_time[s] = now

                        send(f"🟢 BUY {s} @ {price} | Score:{score} | P:{round(pattern_score,2)}")

                    # ===== EXIT =====
                    if pos:
                        highest_price[s] = max(highest_price.get(s, price), price)

                        pnl = price - pos["entry"]

                        trail = highest_price[s] * (0.99 if pnl > 1 else 0.985)

                        # 🔥 smart exit
                        if price < trail or score <= -50 or pnl < -3:

                            save_trade(s, pos["entry"], price, pnl)
                            delete_position(s)

                            update_weights(weights, pnl)
                            save_pattern(pattern, pnl)   # 🔥 MEMORY SAVE

                            last_pnl = pnl

                            wr = get_winrate()

                            send(f"🔒 EXIT {s} ₹{round(pnl,2)} | WR:{wr}%")

                            del positions[s]
                            if s in highest_price:
                                del highest_price[s]

                except Exception as e:
                    print("STOCK ERROR:", s, e)

            # ===== HEARTBEAT =====
            if time.time() - last_heartbeat > 1800:
                send("🤖 BOT RUNNING OK")
                last_heartbeat = time.time()

            time.sleep(70)

        except Exception as e:
            send(f"⚠️ ERROR {e}")
            time.sleep(5)

# ===== START =====
if __name__ == "__main__":
    run()
