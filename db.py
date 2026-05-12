from sqlalchemy import create_engine, text
import os

# =========================================================
# DATABASE CONNECTION
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

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
            trades INT,
            avg_profit FLOAT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """))

        # =====================================================
        # POSITIONS TABLE
        # =====================================================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS positions(

            symbol TEXT PRIMARY KEY,
            buy_price FLOAT,
            qty INT,
            highest_price FLOAT,
            partial_booked BOOLEAN,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

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
# SAVE ANALYTICS
# =========================================================

def save_analytics(

    win_rate,
    total_profit,
    trades,
    avg_profit

):

    with engine.begin() as conn:

        conn.execute(text("""

        INSERT INTO analytics(
            win_rate,
            total_profit,
            trades,
            avg_profit
        )

        VALUES(
            :w,
            :p,
            :t,
            :a
        )

        """), {

            "w": win_rate,
            "p": total_profit,
            "t": trades,
            "a": avg_profit

        })

# =========================================================
# SAVE POSITION
# =========================================================

def save_position(
    symbol,
    buy_price,
    qty,
    highest_price,
    partial_booked=False
):

    with engine.begin() as conn:

        conn.execute(text("""

        INSERT INTO positions(
            symbol,
            buy_price,
            qty,
            highest_price,
            partial_booked
        )

        VALUES(
            :s,
            :bp,
            :q,
            :hp,
            :pb
        )

        ON CONFLICT(symbol)

        DO UPDATE SET

            buy_price = EXCLUDED.buy_price,
            qty = EXCLUDED.qty,
            highest_price = EXCLUDED.highest_price,
            partial_booked = EXCLUDED.partial_booked

        """), {

            "s": symbol,
            "bp": buy_price,
            "q": qty,
            "hp": highest_price,
            "pb": partial_booked

        })

# =========================================================
# DELETE POSITION
# =========================================================

def delete_position(symbol):

    with engine.begin() as conn:

        conn.execute(text("""

        DELETE FROM positions

        WHERE symbol = :s

        """), {

            "s": symbol

        })

# =========================================================
# LOAD POSITIONS
# =========================================================

def load_positions():

    with engine.begin() as conn:

        result = conn.execute(text("""

        SELECT
            symbol,
            buy_price,
            qty,
            highest_price,
            partial_booked

        FROM positions

        """))

        rows = result.fetchall()

    positions = {}

    for row in rows:

        positions[row[0]] = {

            "buy_price": float(row[1]),
            "qty": int(row[2]),
            "highest_price": float(row[3]),
            "partial_booked": bool(row[4])

        }

    print("✅ POSITIONS RESTORED")

    return positions
def save_daily_pnl(date, pnl):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_pnl (
            date TEXT PRIMARY KEY,
            pnl REAL
        )
    """)

    cur.execute("""
        INSERT OR REPLACE INTO daily_pnl (date, pnl)
        VALUES (?, ?)
    """, (date, pnl))

    conn.commit()
    conn.close()
# =========================================================
# LIFETIME PERFORMANCE ANALYTICS
# =========================================================

def get_lifetime_stats():

    import sqlite3

    conn = sqlite3.connect("trading.db")

    c = conn.cursor()

    # =========================================
    # CHECK TABLE
    # =========================================

    c.execute("""

        CREATE TABLE IF NOT EXISTS trades (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock TEXT,
            action TEXT,
            price REAL,
            qty INTEGER,
            pnl REAL,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP

        )

    """)

    # =========================================
    # TOTAL TRADES
    # =========================================

    c.execute("""

        SELECT COUNT(*)
        FROM trades
        WHERE action IN ('SELL', 'PARTIAL SELL')

    """)

    total_trades = c.fetchone()[0] or 0

    # =========================================
    # LIFETIME PNL
    # =========================================

    c.execute("""

        SELECT SUM(pnl)
        FROM trades
        WHERE action IN ('SELL', 'PARTIAL SELL')

    """)

    lifetime_pnl = c.fetchone()[0]

    if lifetime_pnl is None:
        lifetime_pnl = 0

    # =========================================
    # WIN TRADES
    # =========================================

    c.execute("""

        SELECT COUNT(*)
        FROM trades
        WHERE pnl > 0
        AND action IN ('SELL', 'PARTIAL SELL')

    """)

    win_trades = c.fetchone()[0] or 0

    # =========================================
    # LOSS TRADES
    # =========================================

    c.execute("""

        SELECT COUNT(*)
        FROM trades
        WHERE pnl <= 0
        AND action IN ('SELL', 'PARTIAL SELL')

    """)

    loss_trades = c.fetchone()[0] or 0

    conn.close()

    # =========================================
    # ACCURACY
    # =========================================

    accuracy = 0

    if total_trades > 0:

        accuracy = round(

            (win_trades / total_trades) * 100,
            2

        )

    return {

        "total_trades": total_trades,
        "lifetime_pnl": round(lifetime_pnl, 2),
        "win_trades": win_trades,
        "loss_trades": loss_trades,
        "accuracy": accuracy

    }
