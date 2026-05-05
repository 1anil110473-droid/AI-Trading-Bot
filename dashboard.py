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
<h2>🔐 Login Dashboard</h2>
<form method="post">
    Username: <input type="text" name="username"><br><br>
    Password: <input type="password" name="password"><br><br>
    <input type="submit" value="Login">
</form>
<p style="color:red;">{{error}}</p>
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

# ===== DASHBOARD =====
@app.route("/")
def home():
    if not is_logged_in():
        return redirect("/login")

    try:
        trades = get_trades()
    except:
        trades = []

    try:
        positions = load_positions()
    except:
        positions = {}

    # SAFE CALC
    pnl = 0
    if trades:
        try:
            pnl = sum([t[3] for t in trades if len(t) > 3])
        except:
            pnl = 0

    try:
        avg = get_avg_reward()
    except:
        avg = 0

    html = f"""
    <h2>🚀 V35 LIVE DASHBOARD</h2>
    <a href="/logout">Logout</a>

    <h3>Total Trades: {len(trades)}</h3>
    <h3>Total PnL: {round(pnl,2)}</h3>
    <h3>Avg Reward: {round(avg,2)}</h3>

    <hr>

    <h3>📌 Open Positions</h3>
    <ul>
    """

    if positions:
        for s,p in positions.items():
            entry = p.get("entry",0)
            qty = p.get("qty",0)
            typ = p.get("type","NA")

            html += f"<li>{s} | Entry:{entry} | Qty:{qty} | {typ}</li>"
    else:
        html += "<li>No open positions</li>"

    html += "</ul><hr><h3>📜 Recent Trades</h3><ul>"

    if trades:
        for t in trades[-10:]:
            try:
                html += f"<li>{t[0]} | Entry:{t[1]} | Exit:{t[2]} | PnL:{t[3]}</li>"
            except:
                continue
    else:
        html += "<li>No trades yet</li>"

    html += "</ul>"

    return html

# ===== API =====
@app.route("/api/stats")
def stats():
    if not is_logged_in():
        return {"error":"unauthorized"},401

    try:
        trades = get_trades()
    except:
        trades = []

    pnl = 0
    if trades:
        try:
            pnl = sum([t[3] for t in trades if len(t)>3])
        except:
            pnl = 0

    return jsonify({
        "trades": len(trades),
        "pnl": pnl,
        "avg_reward": get_avg_reward()
    })

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
