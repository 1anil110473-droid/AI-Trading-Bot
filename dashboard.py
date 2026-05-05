from flask import Flask
from db import get_trades

app = Flask(__name__)

@app.route("/")
def home():
    trades = get_trades()

    total = len(trades)
    wins = len([t for t in trades if t[3] > 0])
    pnl = sum([t[3] for t in trades])

    winrate = (wins/total*100) if total>0 else 0

    return f"""
    <h1>📊 V6 AI BOT</h1>
    <h2>PnL: ₹{round(pnl,2)}</h2>
    <h3>Win Rate: {round(winrate,1)}%</h3>
    <h3>Total Trades: {total}</h3>
    """

app.run(host="0.0.0.0", port=8080)
