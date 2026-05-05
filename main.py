import yfinance as yf
import pandas as pd
import time, os, requests
from db import save_trade

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

positions = {}

STOCKS = [
"HDFCBANK.NS","ICICIBANK.NS","SBIN.NS",
"TCS.NS","INFY.NS","RELIANCE.NS",
"TATASTEEL.NS","CIPLA.NS",
"COFORGE.NS","TRENT.NS"
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
        pass

# ===== SAFE VALUE =====
def safe(x):
    try:
        if hasattr(x, "values"):
            return float(x.values[0])
        return float(x)
    except:
        return 0.0

# ===== DATA =====
def get_df(stock):
    try:
        df = yf.download(stock, period="2d", interval="5m", progress=False)

        if df is None or df.empty or len(df) < 50:
            return None

        return df

    except:
        return None

# ===== INDICATORS =====
def indicators(df):
    df = df.copy()

    # Fix MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df["EMA5"] = df["Close"].ewm(span=5).mean()
    df["EMA15"] = df["Close"].ewm(span=15).mean()

    df["RET"] = df["Close"].pct_change()
    df["RSI"] = df["RET"].rolling(14).mean() * 100

    df["VWAP"] = (df["Close"] * df["Volume"]).cumsum() / df["Volume"].cumsum()

    df = df.dropna()

    return df

# ===== AI SCORE =====
def ai_score(row):
    ema5 = safe(row["EMA5"])
    ema15 = safe(row["EMA15"])
    rsi = safe(row["RSI"])
    close = safe(row["Close"])
    vwap = safe(row["VWAP"])

    score = 0

    if ema5 > ema15:
        score += 40
    else:
        score -= 40

    if rsi > 0:
        score += 30
    else:
        score -= 30

    if close > vwap:
        score += 30
    else:
        score -= 30

    return score

# ===== BOT =====
def run():
    send("🚀 V6 FINAL BOT STARTED")

    while True:
        try:
            for s in STOCKS:
                try:
                    df = get_df(s)
                    if df is None:
                        continue

                    df = indicators(df)

                    if df is None or df.empty:
                        continue

                    last = df.iloc[-1]

                    score = ai_score(last)
                    price = safe(last["Close"])

                    pos = positions.get(s)

                    # ENTRY
                    if score >= 60 and not pos:
                        positions[s] = {"entry": price}
                        send(f"🟢 BUY {s} @ {price} | Score {score}")

                    # EXIT
                    elif pos and score <= -60:
                        pnl = price - pos["entry"]
                        save_trade(s, pos["entry"], price, pnl)
                        send(f"🔁 EXIT {s} ₹{round(pnl,2)}")
                        del positions[s]

                except Exception as stock_error:
                    print("STOCK ERROR:", s, stock_error)

            time.sleep(90)

        except Exception as e:
            print("MAIN ERROR:", e)
            time.sleep(90)

if __name__ == "__main__":
    run()
