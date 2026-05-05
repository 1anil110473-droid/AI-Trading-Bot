from flask import Flask, render_template_string
from db import get_trades, load_positions, get_avg_reward
import json

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🚀 V35 AI Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; background:#111; color:#eee; }
        h2 { color:#00ffcc; }
        .card { background:#1e1e1e; padding:15px; margin:10px; border-radius:10px; }
    </style>
</head>

<body>

<h2>🚀 V35 LIVE DASHBOARD</h2>

<div class="card">
    <p>Total Trades: {{total}}</p>
    <p>Total PnL: {{pnl}}</p>
    <p>Avg Reward: {{reward}}</p>
</div>

<div class="card">
    <h3>📊 PnL Chart</h3>
    <canvas id="pnlChart"></canvas>
</div>

<div class="card">
    <h3>📌 Open Positions</h3>
    <ul>
    {% for k,v in positions.items() %}
        <li>{{k}} | Entry: {{v['entry']}} | Qty: {{v['qty']}} | {{v['type']}}</li>
    {% endfor %}
    </ul>
</div>

<div class="card">
    <h3>📜 Recent Trades</h3>
    <ul>
    {% for t in trades %}
        <li>{{t[0]}} | Entry: {{t[1]}} | Exit: {{t[2]}} | PnL: {{t[3]}}</li>
    {% endfor %}
    </ul>
</div>

<script>
let pnlData = {{ pnl_list | safe }};

let ctx = document.getElementById('pnlChart').getContext('2d');

new Chart(ctx, {
    type: 'line',
    data: {
        labels: pnlData.map((_,i)=>i+1),
        datasets: [{
            label: 'PnL Growth',
            data: pnlData,
            fill: false,
            tension: 0.2
        }]
    }
});
</script>

<meta http-equiv="refresh" content="30">

</body>
</html>
"""

@app.route("/")
def home():
    trades = get_trades()
    positions = load_positions()

    pnl_list = []
    total_pnl = 0

    for t in trades:
        total_pnl += t[3]
        pnl_list.append(total_pnl)

    return render_template_string(
        HTML,
        total=len(trades),
        pnl=round(total_pnl,2),
        reward=round(get_avg_reward(),2),
        trades=trades[-10:],
        positions=positions,
        pnl_list=json.dumps(pnl_list)
    )

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",5000)))
