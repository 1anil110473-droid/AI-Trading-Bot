from sqlalchemy import create_engine, text
import os

# =========================================================
# DATABASE CONNECTION
# =========================================================

engine = create_engine(os.getenv("DATABASE_URL"))

# =========================================================
# INIT DATABASE
# =========================================================

def init_db():

    with engine.begin() as conn:

        # =====================================================
        # TRADES TABLE
        # =====================================================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS trades(

            id SERIAL PRIMARY KEY,
            symbol TEXT,
            action TEXT,
            price FLOAT,
            qty INT,
            pnl FLOAT,
            reason TEXT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """))

        # =====================================================
        # AI WEIGHTS TABLE
        # =====================================================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS ai_weights(

            indicator TEXT PRIMARY KEY,
            weight FLOAT

        )

        """))

        # =====================================================
        # ANALYTICS TABLE
        # =====================================================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS analytics(

            id SERIAL PRIMARY KEY,
            win_rate FLOAT,
            total_profit FLOAT,
            trades INT

        )

        """))

# =========================================================
# SAVE TRADE
# =========================================================

def save_trade(symbol, action, price, qty, pnl, reason):

    with engine.begin() as conn:

        conn.execute(text("""

        INSERT INTO trades(
            symbol,
            action,
            price,
            qty,
            pnl,
            reason
        )

        VALUES(
            :s,
            :a,
            :p,
            :q,
            :pn,
            :r
        )

        """), {

            "s": symbol,
            "a": action,
            "p": price,
            "q": qty,
            "pn": pnl,
            "r": reason

        })

# =========================================================
# LOAD OPEN POSITIONS
# =========================================================

def load_positions():

    with engine.begin() as conn:

        result = conn.execute(text("""

        SELECT
            symbol,
            action,
            price,
            qty

        FROM trades

        ORDER BY id ASC

        """))

        rows = result.fetchall()

    positions = {}

    for row in rows:

        symbol = row[0]
        action = row[1]
        price = float(row[2])
        qty = int(row[3])

        # =====================================================
        # BUY ENTRY
        # =====================================================

        if action == "BUY":

            positions[symbol] = {

                "buy_price": price,
                "qty": qty,
                "highest_price": price,
                "partial_booked": False

            }

        # =====================================================
        # SELL EXIT
        # =====================================================

        elif action == "SELL":

            if symbol in positions:

                del positions[symbol]

    print("✅ POSITIONS RESTORED")

    return positions
