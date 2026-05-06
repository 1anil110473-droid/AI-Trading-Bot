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

# ===== SAFE =====
def safe(x):
    try:
        if hasattr(x,"values"):
            return float(x.values[0])
        return float(x)
    except:
        return 0.0

# ===== TELEGRAM =====
def send(msg):
    try:
        if TOKEN:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          data={"chat_id":CHAT_ID,"text":msg})
    except:
        pass
    print(msg)

# ===== NEWS =====
def news_sentiment():
    try:
        url=f"https://newsapi.org/v2/everything?q=stock&apiKey={NEWS_KEY}"
        r=requests.get(url,timeout=5).json()
        articles=r.get("articles",[])[:5]

        score=0
        for a in articles:
            txt=(a.get("title","")+a.get("description","")).lower()
            if "rise" in txt: score+=1
            if "fall" in txt: score-=1

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

        if isinstance(df.columns,pd.MultiIndex):
            df.columns=df.columns.get_level_values(0)

        return df
    except:
        return None

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

# ===== SCORE =====
def score(r):
    s=0
    s+=weights["EMA"] if safe(r["EMA5"])>safe(r["EMA15"]) else -weights["EMA"]
    s+=weights["RSI"] if safe(r["RSI"])>0 else -weights["RSI"]
    s+=weights["VWAP"] if safe(r["Close"])>safe(r["VWAP"]) else -weights["VWAP"]
    s+=weights["MACD"] if safe(r["MACD"])>safe(r["MACD_SIGNAL"]) else -weights["MACD"]
    s+=weights["VOL"] if safe(r["Volume"])>safe(r["VOL_AVG"]) else -weights["VOL"]
    return s

# ===== TOP 5 =====
STOCKS=[ "HDFCBANK.NS","ICICIBANK.NS","SBIN.NS",
"TCS.NS","INFY.NS","WIPRO.NS","RELIANCE.NS","TATASTEEL.NS",
"HINDZINC.NS","HINDCOPPER.NS","SUNPHARMA.NS","DRREDDY.NS",
"CIPLA.NS","COFORGE.NS","TRENT.NS" ]

def top5():
    lst=[]
    for s in STOCKS:
        df=get_df(s)
        if df is None:continue
        df=indicators(df)
        r=df.iloc[-1]
        sc=score(r)
        lst.append((s,sc))
    lst.sort(key=lambda x:abs(x[1]),reverse=True)
    return [x[0] for x in lst[:5]]

# ===== QTY =====
def qty(price):
    return max(50,min(int(CAPITAL/price),100))

# ===== BOT =====
def run():
    global positions,daily_pnl,trade_count

    send("🚀 FINAL ULTRA BOT STARTED")

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

                    send(f"🟢 ENTRY {s} {typ} @ {price} | SL:{round(sl,2)} | TGT:{round(target,2)} | NEWS:{news}")

                # EXIT
                if pos:
                    pnl=(price-pos["entry"])*pos["qty"]
                    if pos["type"]=="SELL":pnl=-pnl

                    if not pos["partial"] and pnl>200:
                        pos["partial"]=True
                        send(f"💰 PARTIAL {s} ₹{round(pnl/2,2)}")

                    # TRAILING SL
                    if pos["type"]=="BUY":
                        pos["sl"]=max(pos["sl"],price-atr)
                    else:
                        pos["sl"]=min(pos["sl"],price+atr)

                    if price<=pos["sl"] or price>=pos["target"] or sc<-60:
                        save_trade(s,pos["entry"],price,pnl)
                        delete_position(s)

                        daily_pnl+=pnl

                        send(f"🔒 EXIT {s} ₹{round(pnl,2)}")

                        del positions[s]

            # HEARTBEAT (3H)
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
