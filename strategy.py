import pandas as pd

from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volume import VolumeWeightedAveragePrice
from ta.volatility import AverageTrueRange

# =========================================================
# V54 INSTITUTIONAL STRATEGY ENGINE
# =========================================================

def apply_strategy(df, weights):

    if isinstance(df.columns, pd.MultiIndex):

        df.columns = df.columns.get_level_values(0)

    df = df.dropna()

    close = pd.Series(df["Close"]).squeeze()
    high = pd.Series(df["High"]).squeeze()
    low = pd.Series(df["Low"]).squeeze()
    volume = pd.Series(df["Volume"]).squeeze()

    # =====================================================
    # EMA
    # =====================================================

    df["EMA20"] = EMAIndicator(
        close=close,
        window=20
    ).ema_indicator()

    df["EMA50"] = EMAIndicator(
        close=close,
        window=50
    ).ema_indicator()

    # =====================================================
    # RSI
    # =====================================================

    df["RSI"] = RSIIndicator(
        close=close,
        window=14
    ).rsi()

    # =====================================================
    # MACD
    # =====================================================

    macd = MACD(close=close)

    df["MACD"] = macd.macd()
    df["MACD_SIGNAL"] = macd.macd_signal()

    # =====================================================
    # VWAP
    # =====================================================

    vwap = VolumeWeightedAveragePrice(
        high=high,
        low=low,
        close=close,
        volume=volume
    )

    df["VWAP"] = vwap.volume_weighted_average_price()

    # =====================================================
    # ATR
    # =====================================================

    atr = AverageTrueRange(
        high=high,
        low=low,
        close=close,
        window=14
    )

    df["ATR"] = atr.average_true_range()

    # =====================================================
    # LAST CANDLE
    # =====================================================

    last = df.iloc[-1]

    score = 0

    reasons = []

    # =====================================================
    # EMA
    # =====================================================

    if last["EMA20"] > last["EMA50"]:

        score += weights["EMA"]
        reasons.append("EMA Bullish")

    # =====================================================
    # RSI
    # =====================================================

    if last["RSI"] > 55:

        score += weights["RSI"]
        reasons.append("RSI Strong")

    # =====================================================
    # MACD
    # =====================================================

    if last["MACD"] > last["MACD_SIGNAL"]:

        score += weights["MACD"]
        reasons.append("MACD Bullish")

    # =====================================================
    # VWAP
    # =====================================================

    if last["Close"] > last["VWAP"]:

        score += weights["VWAP"]
        reasons.append("Above VWAP")

    # =====================================================
    # VOLUME SPIKE ENGINE
    # =====================================================

    avg_volume = volume.tail(20).mean()

    volume_spike = last["Volume"] > (avg_volume * 1.8)

    if volume_spike:

        score += weights["VOLUME"]
        reasons.append("Volume Spike")

    # =====================================================
    # SUPPORT / RESISTANCE
    # =====================================================

    support = low.tail(20).min()

    resistance = high.tail(20).max()

    # =====================================================
    # SUPPORT HOLDING
    # =====================================================

    if last["Close"] > support * 1.01:

        score += weights["SUPPORT"]
        reasons.append("Support Holding")

    # =====================================================
    # RESISTANCE BREAKOUT
    # =====================================================

    breakout = False

    if (

        last["Close"] > resistance
        and volume_spike

    ):

        breakout = True

        score += weights["BREAKOUT"]

        reasons.append("Resistance Breakout")

    # =====================================================
    # PREVIOUS DAY BREAKOUT
    # =====================================================

    prev_high = high.iloc[-20:-1].max()

    prev_low = low.iloc[-20:-1].min()

    if last["Close"] > prev_high:

        score += 10
        reasons.append("Previous High Breakout")

    if last["Close"] < prev_low:

        score -= 10
        reasons.append("Previous Low Breakdown")

    # =====================================================
    # CONSOLIDATION BREAKOUT
    # =====================================================

    range_percent = (
        (
            resistance - support
        ) / support
    ) * 100

    if (

        range_percent < 2
        and breakout

    ):

        score += 15

        reasons.append("Consolidation Breakout")

    # =====================================================
    # FALSE BREAKOUT FILTER
    # =====================================================

    candle_body = abs(

        last["Close"] - last["Open"]

    )

    candle_range = (

        last["High"] - last["Low"]

    )

    if (

        breakout
        and candle_body < (candle_range * 0.3)

    ):

        score -= 15

        reasons.append("False Breakout Risk")

    # =====================================================
    # ATR VOLATILITY FILTER
    # =====================================================

    atr_percent = (

        last["ATR"] / last["Close"]

    ) * 100

    if atr_percent >= 4:

        score -= 10

        reasons.append("High Volatility Risk")

    # =====================================================
    # VWAP SUPPORT ALIGNMENT
    # =====================================================

    if (

        last["Close"] > last["VWAP"]
        and last["EMA20"] > last["EMA50"]

    ):

        score += 5

        reasons.append("VWAP Trend Alignment")

    # =====================================================
    # FINAL
    # =====================================================

    return {

        "score": max(0, min(100, score)),
        "reasons": reasons,
        "atr": float(last["ATR"]),
        "support": float(support),
        "resistance": float(resistance),
        "volume_spike": volume_spike,
        "breakout": breakout

    }
