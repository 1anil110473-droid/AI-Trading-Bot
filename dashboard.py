from flask import Flask,session,redirect
from db import get_trades

app=Flask(__name__)
app.secret_key="secret"

@app.route("/")
def home():
    trades=get_trades()

    pnl=sum([t[3] for t in trades]) if trades else 0

    rows=""
    for t in trades[:20]:
        rows+=f"<tr><td>{t[0]}</td><td>{t[1]}</td><td>{t[2]}</td><td>{round(t[3],2)}</td></tr>"

    return f"""
    <h2>🚀 AI DASHBOARD</h2>
    <h3>Total Trades: {len(trades)}</h3>
    <h3>Total PnL: ₹{round(pnl,2)}</h3>

    <table border=1>
    <tr><th>Stock</th><th>Entry</th><th>Exit</th><th>PnL</th></tr>
    {rows}
    </table>
    """

app.run(host="0.0.0.0",port=8080)
