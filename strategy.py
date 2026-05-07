import pandas as pd

from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volume import VolumeWeightedAveragePrice

from patterns import detect_patterns

def apply_strategy(df, weights):

    # ==========================================
    # FIX MULTI INDEX
    # ==========================================

    if isinstance(df.columns, pd.MultiIndex):

        df.columns = df.columns.get_level_values(0)

    # ==========================================
    # REMOVE NaN
    # ==========================================

    df = df.dropna()

    # ==========================================
    # FORCE 1D SERIES
    # ==========================================

    close = pd.Series(df["Close"]).squeeze()

    high = pd.Series(df["High"]).squeeze()

    low = pd.Series(df["Low"]).squeeze()

    volume = pd.Series(df["Volume"]).squeeze()

    # ==========================================
    # EMA
    # ==========================================

    df["EMA20"] = EMAIndicator(
        close=close,
        window=20
    ).ema_indicator()

    df["EMA50"] = EMAIndicator(
        close=close,
        window=50
    ).ema_indicator()

    # ==========================================
    # RSI
    # ==========================================

    df["RSI"] = RSIIndicator(
        close=close,
        window=14
    ).rsi()

    # ==========================================
    # MACD
    # ==========================================

    macd = MACD(close=close)

    df["MACD"] = macd.macd()

    df["MACD_SIGNAL"] = macd.macd_signal()

    # ==========================================
    # VWAP
    # ==========================================

    vwap = VolumeWeightedAveragePrice(

        high=high,
        low=low,
        close=close,
        volume=volume

    )

    df["VWAP"] = vwap.volume_weighted_average_price()

    # ==========================================
    # LAST ROW
    # ==========================================

    last = df.iloc[-1]

    score = 0

    reasons = []

    # ==========================================
    # EMA SIGNAL
    # ==========================================

    if last["EMA20"] > last["EMA50"]:

        score += weights["EMA"]

        reasons.append("EMA Bullish Trend")

    # ==========================================
    # RSI SIGNAL
    # ==========================================

    if last["RSI"] > 55:

        score += weights["RSI"]

        reasons.append("RSI Momentum Strong")

    # ==========================================
    # MACD SIGNAL
    # ==========================================

    if last["MACD"] > last["MACD_SIGNAL"]:

        score += weights["MACD"]

        reasons.append("MACD Bullish")

    # ==========================================
    # VWAP SIGNAL
    # ==========================================

    if last["Close"] > last["VWAP"]:

        score += weights["VWAP"]

        reasons.append("Price Above VWAP")

    # ==========================================
    # PATTERN DETECTION
    # ==========================================

    patterns = detect_patterns(df)

    reasons.extend(patterns)

    # ==========================================
    # FINAL RESULT
    # ==========================================

    return score, reasons
