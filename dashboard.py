from flask import Flask
from sqlalchemy import create_engine,text
import os

app=Flask(__name__)

engine=create_engine(os.getenv("DATABASE_URL"))

@app.route("/")

def home():

    with engine.begin() as conn:

        trades=conn.execute(text("""

        SELECT * FROM trades
        ORDER BY id DESC
        LIMIT 20

        """)).fetchall()

    html="""

    <h1>🚀 AI Trading Dashboard</h1>

    """

    for t in trades:

        html+=f"""

        <p>
        {t.symbol} |
        {t.action} |
        ₹{t.price} |
        PNL ₹{t.pnl}
        </p>

        """

    return html
