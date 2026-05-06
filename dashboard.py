from flask import Flask
from db import get_trades, load_positions

app = Flask(__name__)

@app.route("/")
def dashboard():
    trades = get_trades()
    positions = load_positions()

    pnl = sum([t[4] for t in trades]) if trades else 0

    # ===== OPEN POSITIONS =====
    pos_html = ""
    for s,p in positions.items():
        pos_html += f"""
        <tr>
        <td>{s}</td>
        <td>{p['type']}</td>
        <td>{p['entry']}</td>
        <td>{p['qty']}</td>
        <td>{round(p['sl'],2)}</td>
        <td>{round(p['target'],2)}</td>
        </tr>
        """

    # ===== TRADE TABLE =====
    trade_html = ""
    for t in trades[:20]:
        trade_html += f"""
        <tr>
        <td>{t[0]}</td>
        <td>{t[1]}</td>
        <td>{t[2]}</td>
        <td>{t[3]}</td>
        <td>{round(t[4],2)}</td>
        <td>{t[5]}</td>
        <td>{t[6]}</td>
        </tr>
        """

    pnl_data = [t[4] for t in trades[:20]]

    return f"""
    <html>
    <head>
    <title>AI BOT DASHBOARD</title>
    </head>

    <body style="font-family:Arial; text-align:center;">

    <h1>🚀 AI TRADING DASHBOARD</h1>

    <h2>Total Trades: {len(trades)}</h2>
    <h2>Total PnL: ₹{round(pnl,2)}</h2>

    <h3>📌 OPEN POSITIONS</h3>
    <table border=1 style="margin:auto;">
    <tr><th>Stock</th><th>Type</th><th>Entry</th><th>Qty</th><th>SL</th><th>Target</th></tr>
    {pos_html}
    </table>

    <h3>📊 TRADE HISTORY</h3>
    <table border=1 style="margin:auto;">
    <tr><th>Stock</th><th>Type</th><th>Entry</th><th>Exit</th><th>PnL</th><th>Reason</th><th>Time</th></tr>
    {trade_html}
    </table>

    <h3>📈 PnL CHART</h3>
    <canvas id="chart"></canvas>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
    new Chart(document.getElementById('chart'), {{
        type: 'line',
        data: {{
            labels: {list(range(len(pnl_data)))},
            datasets: [{{
                label: 'PnL',
                data: {pnl_data}
            }}]
        }}
    }});
    </script>

    <script>
    setTimeout(()=>location.reload(),5000)
    </script>

    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
