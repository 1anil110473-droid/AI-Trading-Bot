import psycopg2
import os

# ===== CONNECT =====
def connect():
    url = os.getenv("DATABASE_URL")

    if not url:
        raise Exception("❌ DATABASE_URL missing")

    # Railway fix
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    print("✅ DB CONNECTING...")

    return psycopg2.connect(url, sslmode="require")


# ===== SAFE EXECUTE =====
def execute(query, params=None):
    conn = None
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute(query, params or ())
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("❌ DB ERROR:", e)
        if conn:
            conn.rollback()
            conn.close()


# ===== INIT =====
def init_db():
    execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id SERIAL PRIMARY KEY,
        stock TEXT,
        entry REAL,
        exit REAL,
        pnl REAL
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS positions (
        stock TEXT PRIMARY KEY,
        entry REAL,
        qty INTEGER,
        type TEXT
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS ai_weights (
        name TEXT PRIMARY KEY,
        value REAL
    )
    """)

    defaults = {"EMA":25,"RSI":15,"VWAP":20,"MACD":25}

    for k,v in defaults.items():
        execute("""
        INSERT INTO ai_weights (name,value)
        VALUES (%s,%s)
        ON CONFLICT (name) DO NOTHING
        """,(k,v))


# ===== LOAD =====
def load_positions():
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT stock,entry,qty,type FROM positions")
        rows = cur.fetchall()
        conn.close()

        data = {}

        for r in rows:
            entry_price = r[1]

            data[r[0]] = {
                "entry": entry_price,
                "qty": r[2],
                "type": r[3],

                # 🔥 NEW ADDITIONS (error fix)
                "sl": entry_price,         # default SL
                "target": entry_price,     # default target
                "partial": False           # partial booking flag
            }

        return data

    except Exception as e:
        print("LOAD POS ERROR:", e)
        return {}


def load_weights():
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT name,value FROM ai_weights")
        rows = cur.fetchall()
        conn.close()
        return {r[0]:r[1] for r in rows}
    except:
        return {}


def get_trades():
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT stock,entry,exit,pnl FROM trades ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        return rows
    except:
        return []


# ===== SAVE =====
def save_position(stock,entry,qty,typ):
    execute("""
    INSERT INTO positions (stock,entry,qty,type)
    VALUES (%s,%s,%s,%s)
    ON CONFLICT (stock) DO UPDATE
    SET entry=EXCLUDED.entry, qty=EXCLUDED.qty, type=EXCLUDED.type
    """,(stock,entry,qty,typ))


def delete_position(stock):
    execute("DELETE FROM positions WHERE stock=%s",(stock,))


def save_trade(stock,entry,exit,pnl):
    execute("""
    INSERT INTO trades (stock,entry,exit,pnl)
    VALUES (%s,%s,%s,%s)
    """,(stock,entry,exit,pnl))


def update_weights(weights,pnl):
    for k in weights:
        weights[k]+=1 if pnl>0 else -1
        weights[k]=max(5,min(weights[k],50))
        execute("UPDATE ai_weights SET value=%s WHERE name=%s",(weights[k],k))
