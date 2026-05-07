import yfinance as yf

def market_trend():

    nifty = yf.download(

        "^NSEI",
        period="2d",
        interval="15m",
        auto_adjust=True,
        progress=False

    )

    # =========================
    # SAFETY CHECK
    # =========================

    if nifty.empty or len(nifty) < 20:

        return "SIDEWAYS"

    # =========================
    # REMOVE NaN
    # =========================

    nifty = nifty.dropna()

    # =========================
    # SAFE CLOSE VALUE
    # =========================

    close = float(
        nifty["Close"].values[-1]
    )

    # =========================
    # EMA
    # =========================

    ema = float(
        nifty["Close"]
        .rolling(20)
        .mean()
        .values[-1]
    )

    # =========================
    # TREND DETECTION
    # =========================

    if close > ema:

        return "BULLISH"

    elif close < ema:

        return "BEARISH"

    return "SIDEWAYS"
