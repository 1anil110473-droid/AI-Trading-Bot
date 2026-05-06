import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier

MODEL_FILE="ai_model.pkl"

def features(df):
    df=df.copy()
    df["EMA5"]=df["Close"].ewm(5).mean()
    df["EMA15"]=df["Close"].ewm(15).mean()
    df["RSI"]=df["Close"].pct_change().rolling(14).mean()*100
    df["VWAP"]=(df["Close"]*df["Volume"]).cumsum()/df["Volume"].cumsum()
    df["MACD"]=df["Close"].ewm(12).mean()-df["Close"].ewm(26).mean()
    df["ATR"]=(df["High"]-df["Low"]).rolling(14).mean()
    return df.dropna()

def labels(df):
    df["future"]=df["Close"].shift(-3)
    df["y"]=0
    df.loc[df["future"]>df["Close"],"y"]=1
    df.loc[df["future"]<df["Close"],"y"]=-1
    return df.dropna()

def train(df):
    df=features(df)
    df=labels(df)

    X=df[["EMA5","EMA15","RSI","VWAP","MACD","Volume"]]
    y=df["y"]

    m=RandomForestClassifier(n_estimators=120)
    m.fit(X,y)

    joblib.dump(m,MODEL_FILE)

def load():
    try:return joblib.load(MODEL_FILE)
    except:return None

def predict(m,row):
    try:
        X=[[row["EMA5"],row["EMA15"],row["RSI"],row["VWAP"],row["MACD"],row["Volume"]]]
        p=m.predict(X)[0]
        c=max(m.predict_proba(X)[0])
        return p,c
    except:
        return 0,0
