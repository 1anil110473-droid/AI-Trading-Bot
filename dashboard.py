from flask import Flask, request, redirect, session
from db import get_trades
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret123")

USERNAME = os.getenv("DASH_USER", "admin")
PASSWORD = os.getenv("DASH_PASS", "1234")

# ===== LOGIN =====
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        if user == USERNAME and pwd == PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")
        else:
            return """
            <h3>❌ Wrong Username or Password</h3>
            <a href="/">Try Again</a>
            """

    return """
    <html>
    <body style="font-family:Arial;text-align:center;margin-top:100px;">
    <h2>🔐 AI BOT LOGIN</h2>
    <form method="post">
        <input name="username" placeholder="Username"><br><br>
        <input type="password" name="password" placeholder="Password"><br><br>
        <button>Login</button>
    </form>
    </body>
    </html>
    """

# ===== DASHBOARD =====
@app.route("/dashboard")
def dash():
    if not session.get("logged_in"):
        return redirect("/")

    trades = get_trades() or []

    pnl = 0
    for t in trades:
        try:
            pnl += float(t[3])
        except:
            pass

    return f"""
    <html>
    <body style="font-family:Arial;text-align:center;margin-top:50px;">
    
    <a href="/logout" style="float:right;color:red;margin-right:20px;">🔓 Logout</a>

    <h2>🚀 AI BOT DASHBOARD</h2>
    <h3>Total Trades: {len(trades)}</h3>
    <h3>Total PnL: ₹{round(pnl,2)}</h3>

    </body>
    </html>
    """

# ===== LOGOUT =====
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
