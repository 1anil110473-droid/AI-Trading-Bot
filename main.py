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

# ===== SAFE =====
def safe(x):
    try:
        if isinstance(x,(list,np.ndarray)):
            return float(np.array(x).flatten()[0])
        return float(x)
    except:
        return 0.0

# ===== TELEGRAM =====
def send(msg):
    try:
        if TOKEN:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id":CHAT_ID,"text":msg},timeout=5)
    except:
        pass
    print(msg)

# ===== DATA =====
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

# ===== ML =====
def predict(series):
    try:
        series=np.array(series,dtype=float)
        X,y=prepare_data(series)

        if len(X)<20:
            return safe(series[-1])

        if random.random()<0.2:
            model.fit(X,y,epochs=1,verbose=0)

        pred=model.predict(X[-1].reshape(1,10,1),verbose=0)
        return safe(pred)
    except:
        return safe(series[-1])

# ===== BOT =====
def run():
    global equity,peak

    init_db()
    send("🚀 V35 DUAL MODE BOT STARTED")

    while True:
        try:
            global_trend = safe(get_global_trend())
            sector_signals = {}

            # ===== MODE SELECT =====
            mode = "SAFE"
            if global_trend > 0:
                mode = "AGGRESSIVE"

            if mode=="SAFE":
                scan_list = random.sample(STOCKS,5)
                entry_th = 0.03
            else:
                scan_list = STOCKS
                entry_th = 0.02

            for s in scan_list:
                try:
                    d1=get_data(s,"1h")
                    d2=get_data(s,"15m")
                    d3=get_data(s,"5m")

                    if d1 is None or d2 is None or d3 is None:
                        continue

                    price=safe(d3[-1])

                    p1=safe(predict(d1))
                    p2=safe(predict(d2))
                    p3=safe(predict(d3))

                    ml=((p1-price)/price + (p2-price)/price + (p3-price)/price)/3

                    news=safe(get_sentiment(s))
                    rl=safe(get_avg_reward())

                    base_conf = ml + news + rl

                    sector = get_sector(s)
                    sector_signals.setdefault(sector, []).append(base_conf)

                    sec_score = safe(sector_score(sector, sector_signals))

                    confidence = base_conf + (global_trend*0.5) + (sec_score*0.5)

                    pos=positions.get(s)

                    qty=max(1,int((equity*0.1)/price))

                    # ===== ENTRY =====
                    if confidence>entry_th and not pos:
                        positions[s]={"entry":price,"qty":qty,"type":"LONG"}
                        save_position(s,price,qty,"LONG")
                        send(f"🟢 BUY {s} @ {round(price,2)} | Mode:{mode}")

                    elif confidence<-entry_th and not pos:
                        positions[s]={"entry":price,"qty":qty,"type":"SHORT"}
                        save_position(s,price,qty,"SHORT")
                        send(f"🔴 SHORT {s} @ {round(price,2)} | Mode:{mode}")

                    # ===== EXIT =====
                    if pos:
                        pnl=(price-pos["entry"])*pos["qty"]

                        if pos["type"]=="SHORT":
                            pnl=-pnl

                        save_reward(pnl)

                        equity+=pnl
                        peak=max(peak,equity)

                        dd=(peak-equity)/peak

                        # SAFE exit tighter
                        if mode=="SAFE":
                            exit_cond = pnl>600 or pnl<-400 or dd>0.20
                        else:
                            exit_cond = pnl>1000 or pnl<-600 or dd>0.25

                        if exit_cond:
                            save_trade(s,pos["entry"],price,pnl)
                            delete_position(s)

                            send(f"🔒 EXIT {s} ₹{round(pnl,2)} | Mode:{mode}")

                            del positions[s]

                except Exception as e:
                    print("STOCK ERROR:",s,e)

            time.sleep(60)

        except Exception as e:
            send(f"🔥 ERROR {e}")
            time.sleep(5)

if __name__=="__main__":
    run()
