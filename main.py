import os,time,requests,random
import yfinance as yf
from db import *
from model import load,predict,features

TOKEN=os.getenv("TELEGRAM_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")
NEWS_KEY=os.getenv("NEWS_API_KEY")

CAPITAL=200000
TARGET=1000
MAX_TRADES=5

positions={}
daily_pnl=0
trade_count=0

STOCKS=[
"HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","TCS.NS","INFY.NS",
"WIPRO.NS","RELIANCE.NS","TATASTEEL.NS","HINDZINC.NS",
"HINDCOPPER.NS","SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","COFORGE.NS","TRENT.NS"
]

def send(m):
    try:
        if TOKEN:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          data={"chat_id":CHAT_ID,"text":m})
    except: pass
    print(m)

def news():
    try:
        r=requests.get(f"https://newsapi.org/v2/everything?q=stock&apiKey={NEWS_KEY}").json()
        txt=" ".join([a["title"] for a in r["articles"][:5]]).lower()
        if "rise" in txt:return 1
        if "fall" in txt:return -1
        return 0
    except:return 0

def get_df(s):
    try:
        df=yf.download(s,period="2d",interval="5m",progress=False)
        if df is None or len(df)<50:return None
        return df
    except:return None

def top5(m):
    arr=[]
    for s in STOCKS:
        df=get_df(s)
        if df is None:continue
        df=features(df)
        row=df.iloc[-1]
        p,c=predict(m,row)
        arr.append((s,abs(c)))
    arr.sort(key=lambda x:x[1],reverse=True)
    return [x[0] for x in arr[:5]]

def qty(p): return max(50,min(int(CAPITAL/p),100))

def run():
    global positions,daily_pnl,trade_count

    send("🚀 ULTRA AI BOT STARTED")

    init_db()
    positions=load_positions()
    model=load()

    hb=time.time()

    while True:
        try:
            if daily_pnl>=TARGET:
                send("🎯 DAILY TARGET DONE")
                time.sleep(600);continue

            ns=news()
            selected=top5(model)

            for s in selected:
                if trade_count>=MAX_TRADES:break

                df=get_df(s)
                if df is None:continue

                df=features(df)
                row=df.iloc[-1]

                price=float(row["Close"])
                atr=float(row["ATR"])

                pred,conf=predict(model,row)

                pos=positions.get(s)
                q=qty(price)

                # ENTRY
                if not pos:
                    if pred==1 and conf>0.6 and ns>=0: typ="BUY"
                    elif pred==-1 and conf>0.6 and ns<=0: typ="SELL"
                    else:continue

                    sl=price-atr if typ=="BUY" else price+atr
                    tgt=price+2*(price-sl) if typ=="BUY" else price-2*(sl-price)

                    positions[s]={"entry":price,"qty":q,"type":typ,"sl":sl,"target":tgt}
                    save_position(s,price,q,typ,sl,tgt)

                    trade_count+=1

                    send(f"""
🟢 ENTRY
{s} {typ}
Price:{price}
SL:{round(sl,2)}
TGT:{round(tgt,2)}
AI:{round(conf*100,2)}%
News:{ns}
""")

                # EXIT
                if pos:
                    pnl=(price-pos["entry"])*pos["qty"]
                    if pos["type"]=="SELL": pnl=-pnl

                    if price<=pos["sl"] or price>=pos["target"]:
                        save_trade(s,pos["entry"],price,pnl,"SL/TGT")
                        delete_position(s)

                        daily_pnl+=pnl

                        send(f"🔒 EXIT {s} ₹{round(pnl,2)}")

                        del positions[s]

            if time.time()-hb>10800:
                send("❤️ BOT RUNNING (3H)")
                hb=time.time()

            time.sleep(60)

        except Exception as e:
            send(f"🚨 {e}")
            time.sleep(5)

def start():
    while True:
        try:run()
        except Exception as e:
            send(f"🚨 CRASH {e}")
            time.sleep(5)

if __name__=="__main__":
    start()
