import os,time,requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from db import *

# =========================
# ENV
# =========================
TOKEN=os.getenv("TELEGRAM_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
NEWS_KEY=os.getenv("NEWS_API_KEY")

# =========================
# CONFIG
# =========================
CAPITAL=200000
DAILY_TARGET=1000
MAX_TRADES=5
MAX_DRAWDOWN=-2000

positions={}
trade_count=0
daily_pnl=0

# =========================
# WEIGHTS
# =========================
weights={
    "trend":30,
    "momentum":25,
    "meanrev":20,
    "volume":15,
    "news":10
}

# =========================
# IST MARKET TIME CONTROL
# =========================
IST=pytz.timezone("Asia/Kolkata")

HOLIDAYS=["01-26","08-15","10-02"]

def is_market_open():
    now=datetime.now(IST)

    # weekend
    if now.weekday()>=5:
        return False

    # holiday
    if now.strftime("%m-%d") in HOLIDAYS:
        return False

    start=now.replace(hour=9,minute=15,second=0)
    end=now.replace(hour=15,minute=30,second=0)

    if now<start or now>end:
        return False

    return True

# =========================
# TELEGRAM
# =========================
def send(msg):
    try:
        if TOKEN:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id":CHAT_ID,"text":msg}
            )
    except:
        pass
    print(msg)

# =========================
# NEWS
# =========================
def news_sentiment():
    try:
        url=f"https://newsapi.org/v2/everything?q=stock&apiKey={NEWS_KEY}"
        r=requests.get(url,timeout=5).json()

        score=0
        for a in r.get("articles",[])[:5]:
            t=(a.get("title","")+a.get("description","")).lower()
            if "rise" in t:score+=1
            if "fall" in t:score-=1

        return score
    except:
        return 0

# =========================
# DATA
# =========================
def get_df(s):
    try:
        df=yf.download(s,period="2d",interval="5m",progress=False)
        if df is None or len(df)<50:
            return None
        return df
    except:
        return None

# =========================
# INDICATORS
# =========================
def indicators(df):
    df=df.copy()

    df["ema_fast"]=df["Close"].ewm(span=5).mean()
    df["ema_slow"]=df["Close"].ewm(span=20).mean()

    df["rsi"]=df["Close"].pct_change().rolling(14).mean()*100
    df["vwap"]=(df["Close"]*df["Volume"]).cumsum()/df["Volume"].cumsum()

    df["macd"]=df["Close"].ewm(span=12).mean()-df["Close"].ewm(span=26).mean()

    df["vol_avg"]=df["Volume"].rolling(20).mean()

    return df.dropna()

# =========================
# SCORE ENGINE
# =========================
def score(r,news):
    s=0
    s+=weights["trend"] if r["ema_fast"]>r["ema_slow"] else -weights["trend"]
    s+=weights["momentum"] if r["macd"]>0 else -weights["momentum"]
    s+=weights["meanrev"] if r["rsi"]>0 else -weights["meanrev"]
    s+=weights["volume"] if r["Volume"]>r["vol_avg"] else -weights["volume"]
    s+=weights["news"] if news>0 else -weights["news"]
    return s

# =========================
# STOCKS (FULL FIXED)
# =========================
STOCKS=[
"HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","TCS.NS","INFY.NS",
"WIPRO.NS","RELIANCE.NS","TATASTEEL.NS","HINDCOPPER.NS",
"HINDZINC.NS","SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS",
"COFORGE.NS","TRENT.NS"
]

# =========================
# TOP PICKS
# =========================
def top():
    lst=[]
    news=news_sentiment()

    for s in STOCKS:
        df=get_df(s)
        if df is None:
            continue

        df=indicators(df)
        r=df.iloc[-1]

        sc=score(r,news)
        lst.append((s,sc))

    lst.sort(key=lambda x:abs(x[1]),reverse=True)
    return [x[0] for x in lst[:3]]

# =========================
# QTY
# =========================
def qty(price):
    return max(10,int((CAPITAL*0.01)/price))

# =========================
# RISK
# =========================
def risk_ok():
    global daily_pnl
    if daily_pnl<=MAX_DRAWDOWN:
        send("⛔ DRAWDOWN HIT - BOT PAUSED")
        time.sleep(300)
        return False
    return True

# =========================
# ENTRY SIGNAL
# =========================
def entry_signal(sc):
    if sc>80:
        return "BUY"
    if sc<-80:
        return "SELL"
    return None

# =========================
# BOT
# =========================
def run():

    global positions,trade_count,daily_pnl

    send("🚀 AI TRADING ENGINE STARTED")

    init_db()

    try:
        positions=load_positions()
    except:
        positions={}

    while True:

        try:

            # ================= MARKET FILTER =================
            if not is_market_open():
                time.sleep(300)
                continue

            if not risk_ok():
                continue

            selected=top()

            for s in selected:

                if trade_count>=MAX_TRADES:
                    break

                df=get_df(s)
                if df is None:
                    continue

                df=indicators(df)
                r=df.iloc[-1]

                price=r["Close"]
                sc=score(r,news_sentiment())

                pos=positions.get(s)

                # ================= ENTRY =================
                if not pos:

                    typ=entry_signal(sc)
                    if not typ:
                        continue

                    sl=price*0.99 if typ=="BUY" else price*1.01
                    target=price*1.02 if typ=="BUY" else price*0.98

                    positions[s]={
                        "entry":price,
                        "qty":qty(price),
                        "type":typ,
                        "sl":sl,
                        "target":target
                    }

                    save_position(s,price,qty(price),typ)
                    trade_count+=1

                    send(f"🟢 ENTRY {s} {typ} @ {price}")

                # ================= EXIT =================
                else:

                    pnl=(price-pos["entry"])*pos["qty"]
                    if pos["type"]=="SELL":
                        pnl=-pnl

                    if price<=pos["sl"] or price>=pos["target"] or abs(sc)<30:

                        save_trade(s,pos["entry"],price,pnl)
                        delete_position(s)

                        daily_pnl+=pnl

                        send(f"🔒 EXIT {s} ₹{round(pnl,2)}")

                        positions.pop(s,None)

            time.sleep(60)

        except Exception as e:
            send(f"🚨 ERROR {e}")
            time.sleep(5)

# =========================
# START
# =========================
if __name__=="__main__":
    run()
