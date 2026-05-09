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

        SELECT * FROM trades
        ORDER BY id DESC
        LIMIT 50

        """)).fetchall()

    html = """
    <h1>🚀 V60 Institutional Dashboard</h1>
    <hr>
    """

    for t in trades:

        html += f"""
        <p>
        {t.symbol} |
        {t.action} |
        ₹{t.price} |
        Qty {t.qty} |
        PNL ₹{t.pnl} |
        {t.reason}
        </p>
        """

    return html
