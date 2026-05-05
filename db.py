import sqlite3

conn = sqlite3.connect("trades.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS trades(
    stock TEXT,
    entry REAL,
    exit REAL,
    pnl REAL
)
""")

conn.commit()

def save_trade(stock, entry, exit_price, pnl):
    c.execute("INSERT INTO trades VALUES (?,?,?,?)",
              (stock, entry, exit_price, pnl))
    conn.commit()

def get_trades():
    return c.execute("SELECT * FROM trades").fetchall()
