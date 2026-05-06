import psycopg2
import os

def connect():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id SERIAL PRIMARY KEY,
        stock TEXT,
        entry REAL,
        exit REAL,
        pnl REAL
    )
    """)

    conn.commit()
    conn.close()

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

    cur.execute("SELECT stock, entry, exit, pnl FROM trades ORDER BY id DESC")
    data = cur.fetchall()

    conn.close()
    return data
