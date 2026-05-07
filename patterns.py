def detect_patterns(df):

    patterns=[]

    c=df.iloc[-1]
    p=df.iloc[-2]

    # Bullish Engulfing

    if (
        p["Close"]<p["Open"]
        and c["Close"]>c["Open"]
        and c["Close"]>p["Open"]
    ):
        patterns.append("Bullish Engulfing")

    # Bearish Engulfing

    if (
        p["Close"]>p["Open"]
        and c["Close"]<c["Open"]
        and c["Open"]>p["Close"]
    ):
        patterns.append("Bearish Engulfing")

    return patterns
