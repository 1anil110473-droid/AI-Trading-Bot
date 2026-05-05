import psycopg2, os

def connect():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn=connect();cur=conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS trades(
        id SERIAL PRIMARY KEY,
        stock TEXT,
        entry REAL,
        exit REAL,
        pnl REAL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS positions(
        stock TEXT PRIMARY KEY,
        entry REAL,
        qty REAL,
        type TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS rewards(
        id SERIAL PRIMARY KEY,
        value REAL
    )""")

    conn.commit();conn.close()

# ===== TRADES =====
def save_trade(s,e,x,p):
    conn=connect();cur=conn.cursor()
    cur.execute("INSERT INTO trades(stock,entry,exit,pnl) VALUES(%s,%s,%s,%s)",(s,e,x,p))
    conn.commit();conn.close()

def get_trades():
    conn=connect();cur=conn.cursor()
    cur.execute("SELECT stock,entry,exit,pnl FROM trades")
    data=cur.fetchall()
    conn.close()
    return data

# ===== POSITIONS =====
def save_position(s,e,q,t):
    conn=connect();cur=conn.cursor()
    cur.execute("""
    INSERT INTO positions(stock,entry,qty,type)
    VALUES(%s,%s,%s,%s)
    ON CONFLICT (stock) DO UPDATE SET entry=%s, qty=%s, type=%s
    """,(s,e,q,t,e,q,t))
    conn.commit();conn.close()

def delete_position(s):
    conn=connect();cur=conn.cursor()
    cur.execute("DELETE FROM positions WHERE stock=%s",(s,))
    conn.commit();conn.close()

def load_positions():
    conn=connect();cur=conn.cursor()
    cur.execute("SELECT stock,entry,qty,type FROM positions")
    rows=cur.fetchall()
    conn.close()
    return {r[0]:{"entry":r[1],"qty":r[2],"type":r[3]} for r in rows}

# ===== RL =====
def save_reward(val):
    conn=connect();cur=conn.cursor()
    cur.execute("INSERT INTO rewards(value) VALUES(%s)",(val,))
    conn.commit();conn.close()

def get_avg_reward():
    conn=connect();cur=conn.cursor()
    cur.execute("SELECT AVG(value) FROM rewards")
    r=cur.fetchone()[0]
    conn.close()
    return r if r else 0
