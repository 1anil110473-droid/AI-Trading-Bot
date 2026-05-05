from flask import Flask, jsonify, request, redirect, session, render_template_string
import os

# SAFE IMPORT
try:
    from db import get_trades, load_positions, get_avg_reward
except:
    from db import get_trades, load_positions
    def get_avg_reward():
        return 0

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret123")

USERNAME = os.getenv("DASH_USER", "admin")
PASSWORD = os.getenv("DASH_PASS", "1234")

# ===== LOGIN PAGE =====
login_page = """
<!DOCTYPE html>
<html>
<head>
<title>Login</title>
<style>
body { background:#111; color:#fff; font-family:Arial; text-align:center; margin-top:100px; }
input { padding:10px; margin:5px; }
button { padding:10px 20px; }
</style>
</head>
<body>
<h2>🔐 V37 Login</h2>
<form method="post">
<input name="username" placeholder="Username"><br>
<input name="password" type="password" placeholder="Password"><br>
<button type="submit">Login</button>
</form>
<p style="color:red;">{{error}}</p>
</body>
</html>
"""

# ===== AUTH =====
def is_logged_in():
    return session.get("logged_in")

@app.route("/login", methods=["GET","POST"])
def login():
    error=""
    if request.method=="POST":
        if request.form.get("username")==USERNAME and request.form.get("password")==PASSWORD:
            session["logged_in"]=True
            return redirect("/")
        else:
            error="Invalid Credentials"
    return render_template_string(login_page, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ===== API =====
@app.route("/api/data")
def data():
    if not is_logged_in():
        return {"error":"unauthorized"},401

    trades = get_trades() or []
    positions = load_positions() or []

    pnl_list = []
    equity = 0

    for t in trades:
        try:
            pnl = float(t[3])
            equity += pnl
            pnl_list.append(equity)
        except:
            continue

    return jsonify({
        "trades": trades[-20:],
        "positions": positions,
        "pnl_curve": pnl_list,
        "total_pnl": equity,
        "avg_reward": get_avg_reward()
    })

# ===== DASHBOARD UI =====
@app.route("/")
def home():
    if not is_logged_in():
        return redirect("/login")

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>V37 Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body { background:#0b0b0b; color:#eee; font-family:Arial; }
.container { width:90%; margin:auto; }
.card { background:#1a1a1a; padding:15px; margin:10px 0; border-radius:10px; }
h2 { color:#00ffcc; }
table { width:100%; border-collapse:collapse; }
td, th { padding:8px; border-bottom:1px solid #333; }
.green { color:#00ff00; }
.red { color:#ff4444; }
</style>
</head>

<body>
<div class="container">
<h2>🚀 V37 PRO DASHBOARD</h2>
<a href="/logout">Logout</a>

<div class="card">
<h3>Total PnL: <span id="pnl"></span></h3>
<h3>Avg Reward: <span id="avg"></span></h3>
</div>

<div class="card">
<canvas id="chart"></canvas>
</div>

<div class="card">
<h3>📌 Open Positions</h3>
<table id="pos"></table>
</div>

<div class="card">
<h3>📜 Trades</h3>
<table id="trades"></table>
</div>
</div>

<script>
let chart;

async function loadData(){
    const res = await fetch('/api/data');
    const data = await res.json();

    document.getElementById("pnl").innerText = data.total_pnl.toFixed(2);
    document.getElementById("avg").innerText = data.avg_reward.toFixed(2);

    // ===== POSITIONS =====
    let pos_html = "<tr><th>Stock</th><th>Entry</th><th>Qty</th><th>Type</th></tr>";
    for(let s in data.positions){
        let p = data.positions[s];
        pos_html += `<tr>
            <td>${s}</td>
            <td>${p.entry}</td>
            <td>${p.qty}</td>
            <td>${p.type}</td>
        </tr>`;
    }
    document.getElementById("pos").innerHTML = pos_html;

    // ===== TRADES =====
    let t_html = "<tr><th>Stock</th><th>Entry</th><th>Exit</th><th>PnL</th></tr>";
    data.trades.forEach(t=>{
        let color = t[3] >= 0 ? "green" : "red";
        t_html += `<tr>
            <td>${t[0]}</td>
            <td>${t[1]}</td>
            <td>${t[2]}</td>
            <td class="${color}">${t[3]}</td>
        </tr>`;
    });
    document.getElementById("trades").innerHTML = t_html;

    // ===== CHART =====
    if(chart) chart.destroy();

    chart = new Chart(document.getElementById("chart"), {
        type: 'line',
        data: {
            labels: data.pnl_curve.map((_,i)=>i),
            datasets: [{
                label: 'Equity Curve',
                data: data.pnl_curve,
                borderColor: '#00ffcc',
                fill: false
            }]
        }
    });
}

// AUTO REFRESH
setInterval(loadData, 5000);
loadData();
</script>

</body>
</html>
""")

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
