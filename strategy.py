import pandas as pd

from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volume import VolumeWeightedAveragePrice
from ta.volatility import AverageTrueRange

# =========================================================
# V55 INSTITUTIONAL STRATEGY ENGINE
# UPGRADED + SAFE EXIT SUPPORT
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

    ema_bullish = False
    ema_bearish = False

    if last["EMA20"] > last["EMA50"]:

        ema_bullish = True

        score += weights["EMA"]

        reasons.append("EMA Bullish")

    elif last["EMA20"] < last["EMA50"]:

        ema_bearish = True

        reasons.append("EMA Bearish")

    # =====================================================
    # RSI
    # =====================================================

    if last["RSI"] > 55:

        score += weights["RSI"]

        reasons.append("RSI Strong")

    elif last["RSI"] < 40:

        reasons.append("RSI Weak")

    # =====================================================
    # MACD
    # =====================================================

    if last["MACD"] > last["MACD_SIGNAL"]:

        score += weights["MACD"]

        reasons.append("MACD Bullish")

    else:

        reasons.append("MACD Bearish")

    # =====================================================
    # VWAP
    # =====================================================

    if last["Close"] > last["VWAP"]:

        score += weights["VWAP"]

        reasons.append("Above VWAP")

    else:

        reasons.append("Below VWAP")

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
    # RESISTANCE REJECTION
    # =====================================================

    resistance_rejection = False

    if (

        last["High"] >= resistance * 0.998
        and last["Close"] < resistance
        and last["Close"] < last["Open"]

    ):

        resistance_rejection = True

        reasons.append("Resistance Rejection")

    # =====================================================
    # SUPPORT BOUNCE
    # =====================================================

    bounce = False

    if (

        last["Low"] <= support * 1.002
        and last["Close"] > support

    ):

        bounce = True

        reasons.append("Support Bounce")

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
    # FINAL SCORE SAFETY
    # =====================================================

    final_score = max(0, min(100, score))

    # =====================================================
    # FINAL RETURN
    # =====================================================

    return {

        "score": final_score,

        "reasons": reasons,

        "atr": float(last["ATR"]),

        "atr_percent": float(atr_percent),

        "support": float(support),

        "resistance": float(resistance),

        "vwap": float(last["VWAP"]),

        "ema20": float(last["EMA20"]),

        "ema50": float(last["EMA50"]),

        "ema_bullish": ema_bullish,

        "ema_bearish": ema_bearish,

        "volume_spike": volume_spike,

        "breakout": breakout,

        "bounce": bounce,

        "resistance_rejection": resistance_rejection

    }
