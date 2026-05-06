import yfinance as yf

def backtest():
    df=yf.download("RELIANCE.NS",period="1y")
    capital=100000
    pos=None

    for i,row in df.iterrows():
        if not pos and row["Close"]>row["Close"].rolling(10).mean()[i]:
            pos=row["Close"]

        elif pos and row["Close"]<row["Close"].rolling(10).mean()[i]:
            capital+=row["Close"]-pos
            pos=None

    print("Final:",capital)

backtest()
