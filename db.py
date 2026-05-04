import psycopg2, os

def connect():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = connect(); cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS trades(
    id SERIAL PRIMARY KEY, stock TEXT, entry REAL, exit REAL, pnl REAL)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS positions(
    stock TEXT PRIMARY KEY, entry REAL)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS ai_weights(
    name TEXT PRIMARY KEY, value REAL)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS patterns(
    pattern TEXT PRIMARY KEY, score REAL DEFAULT 0.5, count INT DEFAULT 0)""")

    conn.commit(); conn.close()
    init_weights()

def init_weights():
    conn=connect(); cur=conn.cursor()
    for k,v in {"EMA":25,"RSI":15,"VWAP":20,"MACD":25}.items():
        cur.execute("INSERT INTO ai_weights VALUES(%s,%s) ON CONFLICT DO NOTHING",(k,v))
    conn.commit(); conn.close()

def load_weights():
    conn=connect(); cur=conn.cursor()
    cur.execute("SELECT name,value FROM ai_weights")
    d={k:v for k,v in cur.fetchall()}
    conn.close(); return d

def update_weights(weights,pnl):
    conn=connect(); cur=conn.cursor()
    for k in weights:
        weights[k]+=0.5 if pnl>0 else -0.5
        weights[k]=max(5,min(50,weights[k]))
        cur.execute("UPDATE ai_weights SET value=%s WHERE name=%s",(weights[k],k))
    conn.commit(); conn.close()

def save_pattern(p,pnl):
    conn=connect(); cur=conn.cursor()
    cur.execute("""
    INSERT INTO patterns(pattern,score,count)
    VALUES(%s,0.5,1)
    ON CONFLICT(pattern) DO UPDATE
    SET score = patterns.score + %s,
        count = patterns.count + 1
    """,(p, 0.1 if pnl>0 else -0.1))
    conn.commit(); conn.close()

def get_pattern_score(p):
    conn=connect(); cur=conn.cursor()
    cur.execute("SELECT score FROM patterns WHERE pattern=%s",(p,))
    r=cur.fetchone()
    conn.close()
    return r[0] if r else 0.5

# बाकी same (trades/positions)
def save_trade(s,e,x,p):
    conn=connect(); cur=conn.cursor()
    cur.execute("INSERT INTO trades(stock,entry,exit,pnl) VALUES(%s,%s,%s,%s)",(s,e,x,p))
    conn.commit(); conn.close()

def save_position(s,e):
    conn=connect(); cur=conn.cursor()
    cur.execute("INSERT INTO positions VALUES(%s,%s) ON CONFLICT DO NOTHING",(s,e))
    conn.commit(); conn.close()

def delete_position(s):
    conn=connect(); cur=conn.cursor()
    cur.execute("DELETE FROM positions WHERE stock=%s",(s,))
    conn.commit(); conn.close()

def load_positions():
    conn=connect(); cur=conn.cursor()
    cur.execute("SELECT stock,entry FROM positions")
    d={r[0]:{"entry":r[1]} for r in cur.fetchall()}
    conn.close(); return d

def get_trades():
    conn=connect(); cur=conn.cursor()
    cur.execute("SELECT * FROM trades")
    d=cur.fetchall()
    conn.close(); return d
