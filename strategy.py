from ta.trend import EMAIndicator,MACD
from ta.momentum import RSIIndicator
from ta.volume import VolumeWeightedAveragePrice

from patterns import detect_patterns

def apply_strategy(df,weights):

    df["EMA20"]=EMAIndicator(df["Close"],20).ema_indicator()
    df["EMA50"]=EMAIndicator(df["Close"],50).ema_indicator()

    df["RSI"]=RSIIndicator(df["Close"],14).rsi()

    macd=MACD(df["Close"])

    df["MACD"]=macd.macd()
    df["MACD_SIGNAL"]=macd.macd_signal()

    vwap=VolumeWeightedAveragePrice(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        volume=df["Volume"]
    )

    df["VWAP"]=vwap.volume_weighted_average_price()

    last=df.iloc[-1]

    score=0

    reasons=[]

    if last["EMA20"]>last["EMA50"]:

        score+=weights["EMA"]

        reasons.append("EMA Bullish Trend")

    if last["RSI"]>55:

        score+=weights["RSI"]

        reasons.append("RSI Momentum Strong")

    if last["MACD"]>last["MACD_SIGNAL"]:

        score+=weights["MACD"]

        reasons.append("MACD Bullish")

    if last["Close"]>last["VWAP"]:

        score+=weights["VWAP"]

        reasons.append("Price Above VWAP")

    patterns=detect_patterns(df)

    reasons.extend(patterns)

    return score,reasons
