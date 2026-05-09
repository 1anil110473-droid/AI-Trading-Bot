from flask import Flask
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

@app.route("/")

def home():

    with engine.begin() as conn:

        trades = conn.execute(text("""

        SELECT *
        FROM trades
        ORDER BY id DESC
        LIMIT 20

        """)).fetchall()

    html = """

    <h1>🚀 V50 Institutional Dashboard</h1>

    <h3>Recent Trades</h3>

    """

    for t in trades:

        html += f"""

        <p>

        {t.symbol} |
        {t.action} |
        ₹{round(t.price,2)} |
        Qty {t.qty} |
        PNL ₹{round(t.pnl,2)} |
        {t.reason}

        </p>

        """

    return html

@app.route("/health")

def health():

    return {

        "status": "ok",
        "engine": "running",
        "dashboard": "active"

    }
