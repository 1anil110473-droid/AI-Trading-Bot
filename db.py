from sqlalchemy import create_engine, text
import os
import json
import numpy as np

def clean_signals(signals):

    if not signals:
        return None

    cleaned = {}

    for k, v in signals.items():

        if isinstance(v, (np.bool_, bool)):
            cleaned[k] = bool(v)

        elif isinstance(v, (np.integer,)):
            cleaned[k] = int(v)

        elif isinstance(v, (np.floating,)):
            cleaned[k] = float(v)

        else:
            cleaned[k] = v

    return cleaned

# =========================================================
# DATABASE CONNECTION
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(

    DATABASE_URL,

    pool_pre_ping=True,

    pool_recycle=300,

    pool_size=5,

    max_overflow=10,

    pool_timeout=30,

    connect_args={
        "sslmode": "require"
    }

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
            signals JSON,
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
            signals JSON,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

        """))

# =========================================================
# SAVE TRADE
# =========================================================

def save_trade(
    symbol,
    action,
    price,
    qty,
    pnl,
    reason,
    signals=None
):

    signals = clean_signals(signals)

    with engine.begin() as conn:

        conn.execute(text("""

        INSERT INTO trades(
            symbol,
            action,
            price,
            qty,
            pnl,
            reason,
            signals
        )

        VALUES(
            :s,
            :a,
            :p,
            :q,
            :pn,
            :r,
            :sg
        )

        """), {

            "s": symbol,
            "a": action,
            "p": price,
            "q": qty,
            "pn": pnl,
            "r": reason,

            "sg": json.dumps(signals)
            if signals else None

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
    partial_booked=False,
    signals=None
):

    signals = clean_signals(signals) 
    
    with engine.begin() as conn:

        conn.execute(text("""

        INSERT INTO positions(
            symbol,
            buy_price,
            qty,
            highest_price,
            partial_booked,
            signals
        )

        VALUES(
            :s,
            :bp,
            :q,
            :hp,
            :pb,
            :sg
        )

        ON CONFLICT(symbol)

        DO UPDATE SET

            buy_price = EXCLUDED.buy_price,
            qty = EXCLUDED.qty,
            highest_price = EXCLUDED.highest_price,
            partial_booked = EXCLUDED.partial_booked,
            signals = EXCLUDED.signals

        """), {

            "s": symbol,
            "bp": buy_price,
            "q": qty,
            "hp": highest_price,
            "pb": partial_booked,
            "sg": json.dumps(signals) if signals else None

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
            partial_booked,
            signals

        FROM positions

        """))

        rows = result.fetchall()

    positions = {}

    for row in rows:

        positions[row[0]] = {

            "buy_price": float(row[1]),
            "qty": int(row[2]),
            "highest_price": float(row[3]),
            "partial_booked": bool(row[4]),
            "signals": json.loads(row[5]) if row[5] else {}

        }

    print("✅ POSITIONS RESTORED")

    return positions

# =========================================================
# DAILY PNL DATABASE
# =========================================================

def update_daily_pnl(date, pnl):

    with engine.begin() as conn:

        # =============================================
        # CREATE TABLE
        # =============================================

        conn.execute(text("""

        CREATE TABLE IF NOT EXISTS daily_pnl(

            date TEXT PRIMARY KEY,
            pnl FLOAT

        )

        """))

        # =============================================
        # INSERT / UPDATE
        # =============================================

        conn.execute(text("""

        INSERT INTO daily_pnl(
            date,
            pnl
        )

        VALUES(
            :d,
            :p
        )

        ON CONFLICT(date)

        DO UPDATE SET

            pnl = EXCLUDED.pnl

        """), {

            "d": date,
            "p": pnl

        })


# =========================================================
# LIFETIME PERFORMANCE ANALYTICS
# =========================================================

def get_lifetime_stats():

    with engine.begin() as conn:

        # =============================================
        # TOTAL TRADES
        # =============================================

        result = conn.execute(text("""

        SELECT COUNT(*)

        FROM trades

        WHERE action IN (
            'SELL',
            'PARTIAL SELL'
        )

        """))

        total_trades = result.scalar() or 0

        # =============================================
        # LIFETIME PNL
        # =============================================

        result = conn.execute(text("""

        SELECT SUM(pnl)

        FROM trades

        WHERE action IN (
            'SELL',
            'PARTIAL SELL'
        )

        """))

        lifetime_pnl = result.scalar()

        if lifetime_pnl is None:

            lifetime_pnl = 0

        # =============================================
        # WIN TRADES
        # =============================================

        result = conn.execute(text("""

        SELECT COUNT(*)

        FROM trades

        WHERE pnl > 0

        AND action IN (
            'SELL',
            'PARTIAL SELL'
        )

        """))

        win_trades = result.scalar() or 0

        # =============================================
        # LOSS TRADES
        # =============================================

        result = conn.execute(text("""

        SELECT COUNT(*)

        FROM trades

        WHERE pnl <= 0

        AND action IN (
            'SELL',
            'PARTIAL SELL'
        )

        """))

        loss_trades = result.scalar() or 0

    # =============================================
    # ACCURACY
    # =============================================

    accuracy = 0

    if total_trades > 0:

        accuracy = round(

            (win_trades / total_trades) * 100,
            2

        )

    return {

        "total_trades": total_trades,
        "lifetime_pnl": round(float(lifetime_pnl), 2),
        "win_trades": win_trades,
        "loss_trades": loss_trades,
        "accuracy": accuracy

    }
    
