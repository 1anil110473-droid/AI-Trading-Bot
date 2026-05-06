import psycopg2
import os

def connect():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise Exception("DATABASE_URL not set")
    return psycopg2.connect(url)

def init_db():
    conn = connect()
    cur = conn.cursor()

    # ===== TRADES =====
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id SERIAL PRIMARY KEY,
        stock TEXT,
        entry REAL,
        exit REAL,
        pnl REAL
    )
    """)

    # ===== POSITIONS (🔥 UPDATED WITH QTY) =====
    cur.execute("""
    CREATE TABLE IF NOT EXISTS positions (
        stock TEXT PRIMARY KEY,
        entry REAL,
        qty REAL,
        type TEXT
    )
    """)

    # 🔥 AUTO FIX OLD TABLE
    try:
        cur.execute("ALTER TABLE positions ADD COLUMN qty REAL")
    except:
        pass
    try:
        cur.execute("ALTER TABLE positions ADD COLUMN type TEXT")
    except:
        pass

    # ===== AI WEIGHTS =====
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_weights (
        name TEXT PRIMARY KEY,
        value REAL
    )
    """)

    conn.commit()
    conn.close()

    init_weights()


def init_weights():
    conn = connect()
    cur = conn.cursor()

    defaults = {
        "EMA": 25,
        "RSI": 15,
        "VWAP": 20,
        "MACD": 25
    }

    for k,v in defaults.items():
        cur.execute("""
        INSERT INTO ai_weights (name,value)
        VALUES (%s,%s)
        ON CONFLICT (name) DO NOTHING
        """,(k,v))

    conn.commit()
    conn.close()


def load_weights():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT name,value FROM ai_weights")
    rows = cur.fetchall()

    conn.close()
    return {r[0]: r[1] for r in rows}


def update_weights(weights, pnl):
    conn = connect()
    cur = conn.cursor()

    step = 1

    for k in weights:
        weights[k] += step if pnl > 0 else -step
        weights[k] = max(5, min(50, weights[k]))

        cur.execute("UPDATE ai_weights SET value=%s WHERE name=%s",
                    (weights[k], k))

    conn.commit()
    conn.close()


# ===== CORE =====

def save_trade(stock, entry, exit, pnl):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO trades (stock,entry,exit,pnl) VALUES (%s,%s,%s,%s)",
        (stock,entry,exit,pnl)
    )

    conn.commit()
    conn.close()


def get_trades():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT stock,entry,exit,pnl FROM trades ORDER BY id DESC")
    data = cur.fetchall()

    conn.close()
    return data


def save_position(stock, entry, qty, typ):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO positions (stock,entry,qty,type)
    VALUES (%s,%s,%s,%s)
    ON CONFLICT (stock)
    DO UPDATE SET entry=EXCLUDED.entry, qty=EXCLUDED.qty, type=EXCLUDED.type
    """,(stock,entry,qty,typ))

    conn.commit()
    conn.close()


def delete_position(stock):
    conn = connect()
    cur = conn.cursor()

    cur.execute("DELETE FROM positions WHERE stock=%s",(stock,))

    conn.commit()
    conn.close()


def load_positions():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT stock,entry,qty,type FROM positions")
    rows = cur.fetchall()

    conn.close()

    return {
        r[0]: {"entry":r[1],"qty":r[2],"type":r[3]}
        for r in rows
    }
