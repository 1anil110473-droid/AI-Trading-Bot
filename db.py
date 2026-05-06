import psycopg2
import os

def connect():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise Exception("DATABASE_URL missing")
    return psycopg2.connect(url)

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
        print("DB ERROR:", e)
        if conn:
            conn.rollback()
            conn.close()

# ===== INIT =====
def init_db():
    execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id SERIAL PRIMARY KEY,
        stock TEXT,
        type TEXT,
        entry REAL,
        exit REAL,
        pnl REAL,
        reason TEXT,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS positions (
        stock TEXT PRIMARY KEY,
        type TEXT,
        entry REAL,
        qty INTEGER,
        sl REAL,
        target REAL
    )
    """)

# ===== SAVE =====
def save_trade(stock, typ, entry, exit, pnl, reason):
    execute("""
    INSERT INTO trades (stock,type,entry,exit,pnl,reason)
    VALUES (%s,%s,%s,%s,%s,%s)
    """,(stock,typ,entry,exit,pnl,reason))

def save_position(stock, typ, entry, qty, sl, target):
    execute("""
    INSERT INTO positions (stock,type,entry,qty,sl,target)
    VALUES (%s,%s,%s,%s,%s,%s)
    ON CONFLICT (stock) DO UPDATE
    SET entry=EXCLUDED.entry, qty=EXCLUDED.qty, sl=EXCLUDED.sl, target=EXCLUDED.target
    """,(stock,typ,entry,qty,sl,target))

def delete_position(stock):
    execute("DELETE FROM positions WHERE stock=%s",(stock,))

# ===== LOAD =====
def load_positions():
    try:
        conn=connect()
        cur=conn.cursor()
        cur.execute("SELECT stock,type,entry,qty,sl,target FROM positions")
        rows=cur.fetchall()
        conn.close()

        return {
            r[0]:{
                "type":r[1],
                "entry":r[2],
                "qty":r[3],
                "sl":r[4],
                "target":r[5]
            } for r in rows
        }
    except:
        return {}

def get_trades():
    try:
        conn=connect()
        cur=conn.cursor()
        cur.execute("SELECT stock,type,entry,exit,pnl,reason,time FROM trades ORDER BY id DESC")
        rows=cur.fetchall()
        conn.close()
        return rows
    except:
        return []
