import psycopg2, os

def connect():
    return psycopg2.connect(url, sslmode="require")

def execute(q,p=None):
    conn=connect()
    cur=conn.cursor()
    try:
        cur.execute(q,p or ())
        conn.commit()
    except Exception as e:
        print("DB ERROR:",e)
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def init_db():
    execute("CREATE TABLE IF NOT EXISTS trades(id SERIAL,stock TEXT,entry REAL,exit REAL,pnl REAL)")
    execute("CREATE TABLE IF NOT EXISTS positions(stock TEXT PRIMARY KEY,entry REAL,qty INT,type TEXT)")

def load_positions():
    conn=connect();cur=conn.cursor()
    cur.execute("SELECT stock,entry,qty,type FROM positions")
    rows=cur.fetchall()
    conn.close()
    return {r[0]:{"entry":r[1],"qty":r[2],"type":r[3]} for r in rows}

def save_position(s,e,q,t):
    execute("INSERT INTO positions VALUES(%s,%s,%s,%s) ON CONFLICT(stock) DO UPDATE SET entry=%s,qty=%s,type=%s",(s,e,q,t,e,q,t))

def delete_position(s):
    execute("DELETE FROM positions WHERE stock=%s",(s,))

def save_trade(s,e,x,p):
    execute("INSERT INTO trades(stock,entry,exit,pnl) VALUES(%s,%s,%s,%s)",(s,e,x,p))

def get_trades():
    conn=connect();cur=conn.cursor()
    cur.execute("SELECT stock,entry,exit,pnl FROM trades ORDER BY id DESC")
    rows=cur.fetchall()
    conn.close()
    return rows
