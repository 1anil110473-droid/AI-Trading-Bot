import psycopg2
import os

# ===== CONNECT =====
def connect():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ===== INIT DB =====
def init_db():
    conn = connect()
    cur = conn.cursor()

    # TRADES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id SERIAL PRIMARY KEY,
        stock TEXT,
        entry REAL,
        exit REAL,
        pnl REAL
    )
    """)

    # POSITIONS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS positions (
        stock TEXT PRIMARY KEY,
        entry REAL
    )
    """)

    # AI WEIGHTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ai_weights (
        name TEXT PRIMARY KEY,
        value REAL
    )
    """)

    # PATTERN MEMORY 🔥
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patterns (
        pattern TEXT PRIMARY KEY,
        score REAL DEFAULT 0.5,
        trades INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

    init_weights()

# ===== DEFAULT WEIGHTS =====
def init_weights():
    conn = connect()
    cur = conn.cursor()

    defaults = {
        "EMA": 25,
        "RSI": 15,
        "VWAP": 20,
        "MACD": 25
    }

    for k, v in defaults.items():
        cur.execute("""
        INSERT INTO ai_weights (name, value)
        VALUES (%s,%s)
        ON CONFLICT (name) DO NOTHING
        """, (k, v))

    conn.commit()
    conn.close()

# ===== LOAD WEIGHTS =====
def load_weights():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT name, value FROM ai_weights")
    rows = cur.fetchall()

    conn.close()
    return {r[0]: r[1] for r in rows}

# ===== UPDATE WEIGHTS =====
def update_weights(weights, pnl):
    conn = connect()
    cur = conn.cursor()

    step = 1

    for key in weights:
        if pnl > 0:
            weights[key] += step
        else:
            weights[key] -= step

        weights[key] = max(5, min(weights[key], 50))

        cur.execute("""
        UPDATE ai_weights SET value=%s WHERE name=%s
        """, (weights[key], key))

    conn.commit()
    conn.close()

# ===== PATTERN SAVE =====
def save_pattern(pattern, pnl):
    conn = connect()
    cur = conn.cursor()

    delta = 1 if pnl > 0 else -1

    cur.execute("""
    INSERT INTO patterns (pattern, score, trades)
    VALUES (%s,%s,1)
    ON CONFLICT (pattern)
    DO UPDATE SET
        score = patterns.score + %s,
        trades = patterns.trades + 1
    """, (pattern, delta, delta))

    conn.commit()
    conn.close()

# ===== PATTERN GET =====
def get_pattern_score(pattern):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT score, trades FROM patterns WHERE pattern=%s", (pattern,))
    row = cur.fetchone()

    conn.close()

    if row:
        score, trades = row
        if trades == 0:
            return 0.5
        return score / trades
    return 0.5

# ===== TRADES =====
def save_trade(stock, entry, exit, pnl):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO trades (stock, entry, exit, pnl) VALUES (%s,%s,%s,%s)",
        (stock, entry, exit, pnl)
    )

    conn.commit()
    conn.close()

def get_trades():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT stock, entry, exit, pnl FROM trades")
    data = cur.fetchall()

    conn.close()
    return data

# ===== POSITIONS =====
def save_position(stock, entry):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO positions (stock, entry)
    VALUES (%s,%s)
    ON CONFLICT (stock) DO NOTHING
    """, (stock, entry))

    conn.commit()
    conn.close()

def delete_position(stock):
    conn = connect()
    cur = conn.cursor()

    cur.execute("DELETE FROM positions WHERE stock=%s", (stock,))

    conn.commit()
    conn.close()

def load_positions():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT stock, entry FROM positions")
    rows = cur.fetchall()

    conn.close()
    return {r[0]: {"entry": r[1]} for r in rows}
