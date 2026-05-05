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

# ===== RISK CONTROL =====
def risk_check(confidence):
    global positions

    if len(positions) >= 4:
        return False

    long_count = len([p for p in positions.values() if p["type"]=="LONG"])
    short_count = len([p for p in positions.values() if p["type"]=="SHORT"])

    # block over-direction
    if confidence > 0 and long_count >= 2:
        return False
    if confidence < 0 and short_count >= 2:
        return False

    return True

# ===== BOT =====
def run():
    global equity,peak

    init_db()
    send("🚀 V36 RISK CONTROL BOT STARTED")

    while True:
        try:
            global_trend = safe(get_global_trend())

            # ===== DRAW DOWN STOP =====
            dd = (peak - equity) / peak
            if dd > 0.20:
                send("🛑 DRAW DOWN HIT - BOT PAUSED")
                time.sleep(300)
                continue

            for s in STOCKS:
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
                    sec_score = safe(sector_score(sector,{sector:[base_conf]}))

                    confidence = base_conf + (global_trend*0.5) + (sec_score*0.5)

                    pos=positions.get(s)

                    # ===== POSITION SIZE (5%) =====
                    qty=max(1,int((equity*0.05)/price))

                    # ===== ENTRY =====
                    if not pos and risk_check(confidence):

                        if confidence > 0.03:
                            positions[s]={"entry":price,"qty":qty,"type":"LONG"}
                            save_position(s,price,qty,"LONG")
                            send(f"🟢 BUY {s} @ {round(price,2)}")

                        elif confidence < -0.03:
                            positions[s]={"entry":price,"qty":qty,"type":"SHORT"}
                            save_position(s,price,qty,"SHORT")
                            send(f"🔴 SHORT {s} @ {round(price,2)}")

                    # ===== EXIT =====
                    if pos:
                        pnl=(price-pos["entry"])*pos["qty"]

                        if pos["type"]=="SHORT":
                            pnl=-pnl

                        save_reward(pnl)

                        equity+=pnl
                        peak=max(peak,equity)

                        hold_time = time.time() - pos.get("time", time.time())

                        # smart exit
                        if (
                            pnl > 800 or
                            pnl < -400 or
                            hold_time > 3600 or
                            confidence * (1 if pos["type"]=="LONG" else -1) < 0
                        ):
                            save_trade(s,pos["entry"],price,pnl)
                            delete_position(s)

                            send(f"🔒 EXIT {s} ₹{round(pnl,2)}")

                            del positions[s]

                except Exception as e:
                    print("STOCK ERROR:",s,e)

            time.sleep(60)

        except Exception as e:
            send(f"🔥 ERROR {e}")
            time.sleep(5)

if __name__=="__main__":
    run()
