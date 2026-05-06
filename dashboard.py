from flask import Flask, request, redirect, session
from db import get_trades, load_positions, execute
import os, requests

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret123")

USERNAME = os.getenv("DASH_USER", "admin")
PASSWORD = os.getenv("DASH_PASS", "1234")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# ===== TELEGRAM =====
def send(msg):
    try:
        if TOKEN:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg}
            )
    except:
        pass


# ===== LOGIN PAGE =====
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        if user == USERNAME and pwd == PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")
        else:
            return "<h3>❌ Wrong Username/Password</h3><a href='/'>Try Again</a>"

    return """
    <html>
    <body style="font-family:Arial;text-align:center;margin-top:100px;">
        <h2>🔐 AI BOT LOGIN</h2>
        <form method="post">
            <input name="username" placeholder="Username"><br><br>
            <input type="password" name="password" placeholder="Password"><br><br>
            <button style="padding:10px 20px;">Login</button>
        </form>
    </body>
    </html>
    """


# ===== DASHBOARD =====
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/")

    trades = get_trades() or []
    positions = load_positions() or {}

    pnl = 0
    for t in trades:
        try:
            pnl += float(t[3])
        except:
            pass

    # ===== TRADE TABLE =====
    trade_rows = ""
    for t in trades[:20]:
        trade_rows += f"""
        <tr>
            <td>{t[0]}</td>
            <td>{t[1]}</td>
            <td>{t[2]}</td>
            <td>{round(t[3],2)}</td>
        </tr>
        """

    # ===== POSITION TABLE =====
    pos_rows = ""
    for s, p in positions.items():
        pos_rows += f"""
        <tr>
            <td>{s}</td>
            <td>{p.get("type")}</td>
            <td>{p.get("entry")}</td>
            <td>{p.get("qty")}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;">

    <div style="text-align:right;">
        <a href="/logout" style="color:red;">🔓 Logout</a>
    </div>

    <h2 style="text-align:center;">🚀 AI BOT DASHBOARD</h2>

    <h3 style="text-align:center;">📊 Total Trades: {len(trades)}</h3>
    <h3 style="text-align:center;">💰 Total PnL: ₹{round(pnl,2)}</h3>

    <hr>

    <h3>📈 Open Positions</h3>
    <table border="1" cellpadding="8">
        <tr>
            <th>Stock</th>
            <th>Type</th>
            <th>Entry</th>
            <th>Qty</th>
        </tr>
        {pos_rows}
    </table>

    <hr>

    <h3>📜 Recent Trades</h3>
    <table border="1" cellpadding="8">
        <tr>
            <th>Stock</th>
            <th>Entry</th>
            <th>Exit</th>
            <th>PnL</th>
        </tr>
        {trade_rows}
    </table>

    <br><br>

    <form action="/clean_confirm">
        <button style="padding:10px 20px;background:red;color:white;">
            🔥 CLEAN SYSTEM
        </button>
    </form>

    </body>
    </html>
    """


# ===== CLEAN CONFIRM =====
@app.route("/clean_confirm")
def confirm():
    if not session.get("logged_in"):
        return redirect("/")

    return """
    <h2 style="color:red;">⚠️ Confirm Reset</h2>
    <form action="/clean_db" method="post">
        <button style="padding:10px 20px;background:black;color:white;">
            YES RESET
        </button>
    </form>
    <br><a href="/dashboard">Cancel</a>
    """


# ===== CLEAN DB =====
@app.route("/clean_db", methods=["POST"])
def clean_db():
    if not session.get("logged_in"):
        return redirect("/")

    execute("DELETE FROM positions")
    execute("DELETE FROM trades")
    execute("DELETE FROM ai_weights")

    defaults = {"EMA":25,"RSI":15,"VWAP":20,"MACD":25}

    for k,v in defaults.items():
        execute("INSERT INTO ai_weights (name,value) VALUES (%s,%s)",(k,v))

    send("🔥 FULL RESET DONE")

    return "<h2>✅ RESET DONE</h2><a href='/dashboard'>Back</a>"


# ===== LOGOUT =====
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
