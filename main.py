import os,time,requests,random
import numpy as np
import yfinance as yf

from db import *
from model import create_model,prepare_data
from sentiment import get_sentiment
from global_market import get_global_trend
from sector import get_sector, sector_score

TOKEN=os.getenv("TELEGRAM_TOKEN")
CHAT_ID=os.getenv("CHAT_ID")

CAPITAL=200000
equity=CAPITAL
peak=CAPITAL

positions={}
model=create_model()

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
    except: pass
    print(msg)

def get_data(stock,interval):
    try:
        if interval in ["5m","15m"]:
            period="5d"
        elif interval=="1h":
            period="1mo"
        else:
            period="3mo"

        df=yf.download(stock,period=period,interval=interval,progress=False)

        if df is None or df.empty or len(df)<50:
            return None

        return df["Close"].values
    except:
        return None

def predict(series):
    X,y=prepare_data(series)
    if len(X)<20:
        return series[-1]

    if random.random()<0.2:
        model.fit(X,y,epochs=1,verbose=0)

    pred=model.predict(X[-1].reshape(1,10,1),verbose=0)
    return float(pred[0][0])

def run():
    global equity,peak

    init_db()
    send("🚀 V35 GLOBAL AI STARTED")

    while True:
        try:
            global_trend = get_global_trend()
            sector_signals = {}

            for s in random.sample(STOCKS,5):

                d1=get_data(s,"1h")
                d2=get_data(s,"15m")
                d3=get_data(s,"5m")

                if d1 is None or d2 is None or d3 is None:
                    continue

                price=d3[-1]

                p1,p2,p3=predict(d1),predict(d2),predict(d3)

                ml=((p1-price)/price+(p2-price)/price+(p3-price)/price)/3
                news=get_sentiment(s)
                rl=get_avg_reward()

                base_conf = ml + news + rl

                sector = get_sector(s)
                sector_signals.setdefault(sector, []).append(base_conf)

                sec_score = sector_score(sector, sector_signals)

                confidence = base_conf + (global_trend*0.5) + (sec_score*0.5)

                if global_trend < -0.5:
                    continue

                pos=positions.get(s)
                qty=max(1,int((equity*0.1)/price))

                if confidence>0.02 and not pos:
                    positions[s]={"entry":price,"qty":qty,"type":"LONG"}
                    save_position(s,price,qty,"LONG")
                    send(f"🟢 BUY {s} @ {round(price,2)}")

                elif confidence<-0.02 and not pos:
                    positions[s]={"entry":price,"qty":qty,"type":"SHORT"}
                    save_position(s,price,qty,"SHORT")
                    send(f"🔴 SHORT {s} @ {round(price,2)}")

                if pos:
                    pnl=(price-pos["entry"])*pos["qty"]
                    if pos["type"]=="SHORT":
                        pnl=-pnl

                    save_reward(pnl)

                    equity+=pnl
                    peak=max(peak,equity)

                    dd=(peak-equity)/peak

                    if pnl>800 or pnl<-500 or dd>0.25:
                        save_trade(s,pos["entry"],price,pnl)
                        delete_position(s)

                        send(f"🔒 EXIT {s} ₹{round(pnl,2)} | Eq:{round(equity)}")

                        del positions[s]

            time.sleep(60)

        except Exception as e:
            send(f"ERROR {e}")
            time.sleep(5)

if __name__=="__main__":
    run()
