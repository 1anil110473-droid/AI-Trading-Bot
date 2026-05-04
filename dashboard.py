from flask import Flask, jsonify
from db import get_trades, load_positions, get_avg_reward

app = Flask(__name__)

@app.route("/")
def home():
    return "🚀 V34 BOT LIVE"

@app.route("/stats")
def stats():
    trades = get_trades()
    pnl = sum([t[3] for t in trades]) if trades else 0
    return jsonify({
        "trades": len(trades),
        "pnl": pnl,
        "avg_reward": get_avg_reward()
    })

@app.route("/positions")
def pos():
    return jsonify(load_positions())

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
