import os,time,requests,random
import yfinance as yf
import pandas as pd
from db import *

TOKEN=os.getenv("TELEGRAM_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
NEWS_KEY=os.getenv("NEWS_API_KEY")

CAPITAL=200000
DAILY_TARGET=1000
MAX_TRADES=5

positions={}
weights={"EMA":25,"RSI":15,"MACD":25,"VWAP":20,"VOL":15}

daily_pnl=0
trade_count=0

STOCKS=[
"HDFCBANK.NS","ICICIBANK.NS","SBIN.NS",
"TCS.NS","INFY.NS","WIPRO.NS",
"RELIANCE.NS","TATASTEEL.NS","HINDZINC.NS",
"HINDCOPPER.NS","SUNPHARMA.NS","DRREDDY.NS",
"CIPLA.NS","COFORGE.NS","TRENT.NS"
]

def send(msg):
    try:
        if TOKEN:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          data={"chat_id":CHAT_ID,"text":msg})
    except:
        pass
    print(msg)

def safe(x):
    try:return float(x)
    except:return 0

# ===== NEWS SENTIMENT =====
def news_sentiment():
    try:
        url=f"https://newsapi.org/v2/everything?q=stock%20market&apiKey={NEWS_KEY}"
        r=requests.get(url,timeout=5).json()
        articles=r.get("articles",[])[:5]

        score=0
        for a in articles:
            txt=(a.get("title","")+a.get("description","")).lower()
            if "rise" in txt or "bull" in txt: score+=1
            if "fall" in txt or "crash" in txt: score-=1

        if score>0:return "POSITIVE"
        if score<0:return "NEGATIVE"
        return "NEUTRAL"

    except:
        return random.choice(["POSITIVE","NEGATIVE","NEUTRAL"])

# ===== DATA =====
def get_df(s):
    try:
        df=yf.download(s,period="2d",interval="5m",progress=False)
        if df is None or len(df)<50:return None
        return df
    except:return None

# ===== INDICATORS =====
def indicators(df):
    df=df.copy()
    df["EMA5"]=df["Close"].ewm(span=5).mean()
    df["EMA15"]=df["Close"].ewm(span=15).mean()
    df["RSI"]=df["Close"].pct_change().rolling(14).mean()*100
    df["VWAP"]=(df["Close"]*df["Volume"]).cumsum()/df["Volume"].cumsum()

    df["EMA12"]=df["Close"].ewm(span=12).mean()
    df["EMA26"]=df["Close"].ewm(span=26).mean()
    df["MACD"]=df["EMA12"]-df["EMA26"]
    df["MACD_SIGNAL"]=df["MACD"].ewm(span=9).mean()

    df["ATR"]=(df["High"]-df["Low"]).rolling(14).mean()
    df["VOL_AVG"]=df["Volume"].rolling(20).mean()

    return df.dropna()

# ===== AI SCORE =====
def score(r):
    s=0
    s+=weights["EMA"] if r["EMA5"]>r["EMA15"] else -weights["EMA"]
    s+=weights["RSI"] if r["RSI"]>0 else -weights["RSI"]
    s+=weights["VWAP"] if r["Close"]>r["VWAP"] else -weights["VWAP"]
    s+=weights["MACD"] if r["MACD"]>r["MACD_SIGNAL"] else -weights["MACD"]
    s+=weights["VOL"] if r["Volume"]>r["VOL_AVG"] else -weights["VOL"]
    return s

# ===== LEARNING =====
def update_weights(pnl):
    for k in weights:
        weights[k]+=1 if pnl>0 else -1
        weights[k]=max(5,min(50,weights[k]))

# ===== TOP STOCK =====
def top5():
    lst=[]
    for s in STOCKS:
        df=get_df(s)
        if df is None:continue
        df=indicators(df)
        sc=score(df.iloc[-1])
        lst.append((s,sc))
    lst.sort(key=lambda x:abs(x[1]),reverse=True)
    return [x[0] for x in lst[:5]]

# ===== QTY =====
def qty(price):
    return max(50,min(int(CAPITAL/price),100))

# ===== BOT =====
def run():
    global positions,daily_pnl,trade_count

    send("🚀 V100 ULTRA BOT STARTED")

    init_db()
    positions=load_positions()

    last_heartbeat=time.time()

    while True:
        try:
            news=news_sentiment()
            selected=top5()

            if daily_pnl>=DAILY_TARGET:
                send("🎯 TARGET HIT STOPPED")
                time.sleep(600)
                continue

            for s in selected:
                if trade_count>=MAX_TRADES:break

                df=get_df(s)
                if df is None:continue
                df=indicators(df)

                r=df.iloc[-1]
                price=safe(r["Close"])
                atr=safe(r["ATR"])
                sc=score(r)

                pos=positions.get(s)
                q=qty(price)

                # ENTRY
                if not pos:
                    if sc>60 and news!="NEGATIVE":
                        typ="BUY"
                    elif sc<-60 and news!="POSITIVE":
                        typ="SELL"
                    else:continue

                    sl=price-atr if typ=="BUY" else price+atr
                    target=price+2*(price-sl) if typ=="BUY" else price-2*(sl-price)

                    positions[s]={"entry":price,"qty":q,"type":typ,"sl":sl,"target":target,"partial":False}
                    save_position(s,price,q,typ)
                    trade_count+=1

                    send(f"🟢 ENTRY {s} {typ} @ {price} SL:{round(sl,2)} TGT:{round(target,2)}")

                # EXIT
                if pos:
                    pnl=(price-pos["entry"])*pos["qty"]
                    if pos["type"]=="SELL":pnl=-pnl

                    if not pos["partial"] and pnl>200:
                        pos["partial"]=True
                        send(f"💰 PARTIAL {s} ₹{round(pnl/2,2)}")

                    pos["sl"]=max(pos["sl"],price-atr) if pos["type"]=="BUY" else min(pos["sl"],price+atr)

                    if price<=pos["sl"] or price>=pos["target"] or sc<-60:
                        save_trade(s,pos["entry"],price,pnl)
                        delete_position(s)
                        update_weights(pnl)

                        daily_pnl+=pnl
                        send(f"🔒 EXIT {s} ₹{round(pnl,2)}")

                        del positions[s]

            # HEARTBEAT 3H
            if time.time()-last_heartbeat>10800:
                send("❤️ BOT RUNNING OK (3H)")
                last_heartbeat=time.time()

            time.sleep(60)

        except Exception as e:
            send(f"🚨 ERROR {e}")
            time.sleep(5)

def start():
    while True:
        try:run()
        except Exception as e:
            send(f"🚨 CRASH {e}")
            time.sleep(5)

if __name__=="__main__":
    start()
