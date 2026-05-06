from flask import Flask,session,redirect,request
from db import get_trades

app=Flask(__name__)
app.secret_key="secret"

@app.route("/",methods=["GET","POST"])
def login():
    if request.method=="POST":
        if request.form["u"]=="admin" and request.form["p"]=="1234":
            session["x"]=1
            return redirect("/d")
    return "<form method=post><input name=u><input name=p><button>Login</button></form>"

@app.route("/d")
def d():
    if not session.get("x"): return redirect("/")

    t=get_trades()
    pnl=sum([i[3] for i in t]) if t else 0

    rows="".join([f"<tr><td>{i[0]}</td><td>{i[3]}</td><td>{i[4]}</td></tr>" for i in t])

    return f"""
    <h2>🚀 AI DASHBOARD</h2>
    Trades:{len(t)} | PnL:{round(pnl,2)}
    <table border=1>
    <tr><th>Stock</th><th>PnL</th><th>Reason</th></tr>
    {rows}
    </table>
    <a href='/logout'>Logout</a>
    """

@app.route("/logout")
def lo():
    session.clear()
    return redirect("/")
