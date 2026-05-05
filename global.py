import yfinance as yf

def get_global_trend():
    try:
        sp = yf.download("^GSPC", period="5d", interval="1d", progress=False)
        dow = yf.download("^DJI", period="5d", interval="1d", progress=False)
        nas = yf.download("^IXIC", period="5d", interval="1d", progress=False)

        if sp.empty or dow.empty or nas.empty:
            return 0

        score = 0

        score += 1 if sp["Close"].iloc[-1] > sp["Close"].iloc[-2] else -1
        score += 1 if dow["Close"].iloc[-1] > dow["Close"].iloc[-2] else -1
        score += 1 if nas["Close"].iloc[-1] > nas["Close"].iloc[-2] else -1

        return score / 3

    except:
        return 0
