import psycopg2, os

def conn():
    url=os.getenv("DATABASE_URL")
    if not url: raise Exception("DATABASE_URL missing")
    return psycopg2.connect(url)

def run(q,p=None):
    c=None
    try:
        c=conn();cur=c.cursor()
        cur.execute(q,p or ())
        c.commit()
        cur.close();c.close()
    except Exception as e:
        print("DB ERROR",e)
        if c: c.rollback();c.close()

def init_db():
    run("""CREATE TABLE IF NOT EXISTS trades(
    id SERIAL,stock TEXT,entry REAL,exit REAL,pnl REAL,reason TEXT,time TIMESTAMP DEFAULT NOW())""")

    run("""CREATE TABLE IF NOT EXISTS positions(
    stock TEXT PRIMARY KEY,entry REAL,qty INT,type TEXT,sl REAL,target REAL)""")

def save_trade(s,e,x,p,r):
    run("INSERT INTO trades(stock,entry,exit,pnl,reason) VALUES(%s,%s,%s,%s,%s)",(s,e,x,p,r))

def save_position(s,e,q,t,sl,target):
    run("""INSERT INTO positions VALUES(%s,%s,%s,%s,%s,%s)
    ON CONFLICT(stock) DO UPDATE SET entry=%s,qty=%s,type=%s,sl=%s,target=%s""",
    (s,e,q,t,sl,target,e,q,t,sl,target))

def delete_position(s):
    run("DELETE FROM positions WHERE stock=%s",(s,))

def load_positions():
    try:
        c=conn();cur=c.cursor()
        cur.execute("SELECT * FROM positions")
        r=cur.fetchall();c.close()
        return {i[0]:{"entry":i[1],"qty":i[2],"type":i[3],"sl":i[4],"target":i[5]} for i in r}
    except:return {}

def get_trades():
    try:
        c=conn();cur=c.cursor()
        cur.execute("SELECT stock,entry,exit,pnl,reason,time FROM trades ORDER BY id DESC LIMIT 50")
        r=cur.fetchall();c.close()
        return r
    except:return []
