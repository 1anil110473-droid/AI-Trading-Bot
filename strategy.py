import pandas as pd

from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volume import VolumeWeightedAveragePrice
from ta.volatility import AverageTrueRange

# =========================================================
# INSTITUTIONAL STRATEGY ENGINE
# =========================================================

def apply_strategy(df, weights):

    if isinstance(df.columns, pd.MultiIndex):

        df.columns = df.columns.get_level_values(0)

    df = df.dropna()

    close = pd.Series(df["Close"]).squeeze()
    high = pd.Series(df["High"]).squeeze()
    low = pd.Series(df["Low"]).squeeze()
    volume = pd.Series(df["Volume"]).squeeze()

    df["EMA20"] = EMAIndicator(
        close=close,
        window=20
    ).ema_indicator()

    df["EMA50"] = EMAIndicator(
        close=close,
        window=50
    ).ema_indicator()

    df["RSI"] = RSIIndicator(
        close=close,
        window=14
    ).rsi()

    macd = MACD(close=close)

    df["MACD"] = macd.macd()
    df["MACD_SIGNAL"] = macd.macd_signal()

    vwap = VolumeWeightedAveragePrice(
        high=high,
        low=low,
        close=close,
        volume=volume
    )

    df["VWAP"] = vwap.volume_weighted_average_price()

    atr = AverageTrueRange(
        high=high,
        low=low,
        close=close,
        window=14
    )

    df["ATR"] = atr.average_true_range()

    last = df.iloc[-1]

    score = 0

    reasons = []

    if last["EMA20"] > last["EMA50"]:

        score += weights["EMA"]
        reasons.append("EMA Bullish")

    if last["RSI"] > 55:

        score += weights["RSI"]
        reasons.append("RSI Strong")

    if last["MACD"] > last["MACD_SIGNAL"]:

        score += weights["MACD"]
        reasons.append("MACD Bullish")

    if last["Close"] > last["VWAP"]:

        score += weights["VWAP"]
        reasons.append("Above VWAP")

    return {

        "score": score,
        "reasons": reasons,
        "atr": float(last["ATR"])

    }
