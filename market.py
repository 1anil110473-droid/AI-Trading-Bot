import yfinance as yf

def market_trend():

    nifty=yf.download(
        "^NSEI",
        period="2d",
        interval="15m",
        progress=False
    )

    close=nifty["Close"].iloc[-1]

    ema=nifty["Close"].rolling(20).mean().iloc[-1]

    if close>ema:
        return "BULLISH"

    return "BEARISH"
