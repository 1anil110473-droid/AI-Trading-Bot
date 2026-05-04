# ===== PATTERN MEMORY =====

def save_pattern(pattern, pnl):
    conn = connect()
    cur = conn.cursor()

    # win = +1, loss = -1
    delta = 1 if pnl > 0 else -1

    cur.execute("""
    INSERT INTO patterns (pattern, score, trades)
    VALUES (%s, %s, 1)
    ON CONFLICT (pattern)
    DO UPDATE SET
        score = patterns.score + %s,
        trades = patterns.trades + 1
    """, (pattern, delta, delta))

    conn.commit()
    conn.close()


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
        return score / trades   # normalize
    else:
        return 0.5
