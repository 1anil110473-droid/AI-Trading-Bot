import yfinance as yf
import pandas as pd

# =========================================================
# MARKET TREND ENGINE
# =========================================================

def market_trend():

    try:

        nifty = yf.download(

            "^NSEI",
            period="5d",
            interval="15m",
            auto_adjust=True,
            progress=False,
            threads=False

        )

        if nifty.empty:
            return "SIDEWAYS"

        if isinstance(nifty.columns, pd.MultiIndex):

            nifty.columns = nifty.columns.get_level_values(0)

        nifty = nifty.dropna()

        close = float(nifty["Close"].iloc[-1])

        ema20 = float(
            nifty["Close"]
            .rolling(20)
            .mean()
            .iloc[-1]
        )

        ema50 = float(
            nifty["Close"]
            .rolling(50)
            .mean()
            .iloc[-1]
        )

        if close > ema20 > ema50:
            return "BULLISH"

        if close < ema20 < ema50:
            return "BEARISH"

        return "SIDEWAYS"

    except:

        return "SIDEWAYS"
