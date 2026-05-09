from flask import Flask
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)

engine = create_engine(
    os.getenv("DATABASE_URL"),
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

    html = "<h1>🚀 V51 Institutional Dashboard</h1>"

    for t in trades:

        html += f"""

        <p>
        {t.symbol} |
        {t.action} |
        ₹{t.price} |
        Qty={t.qty} |
        PNL ₹{t.pnl}
        </p>

        """

    return html
