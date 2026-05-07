import yfinance as yf
import pandas as pd

def market_trend():

    try:

        nifty = yf.download(

            "^NSEI",
            period="2d",
            interval="15m",
            auto_adjust=True,
            progress=False

        )

        # =========================
        # EMPTY CHECK
        # =========================

        if nifty.empty or len(nifty) < 20:

            return "SIDEWAYS"

        # =========================
        # REMOVE MULTI INDEX
        # =========================

        if isinstance(nifty.columns, pd.MultiIndex):

            nifty.columns = nifty.columns.get_level_values(0)

        # =========================
        # REMOVE NaN
        # =========================

        nifty = nifty.dropna()

        # =========================
        # CLOSE PRICE
        # =========================

        close = nifty["Close"].iloc[-1]

        # =========================
        # EMA 20
        # =========================

        ema = nifty["Close"].rolling(20).mean().iloc[-1]

        # =========================
        # FLOAT CONVERSION
        # =========================

        close = float(close)

        ema = float(ema)

        # =========================
        # TREND LOGIC
        # =========================

        if close > ema:

            return "BULLISH"

        elif close < ema:

            return "BEARISH"

        return "SIDEWAYS"

    except Exception as e:

        print("MARKET TREND ERROR:", e)

        return "SIDEWAYS"
