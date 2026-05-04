from flask import Flask, jsonify
from db import get_trades, load_positions

app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 BOT RUNNING"

@app.route("/stats")
def stats():
    trades = get_trades()
    total = len(trades)
    pnl = sum([t[4] for t in trades]) if trades else 0
    return jsonify({"trades":total,"pnl":pnl})

@app.route("/positions")
def pos():
    return jsonify(load_positions())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
