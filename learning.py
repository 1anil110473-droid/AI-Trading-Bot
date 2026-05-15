from db import engine
from sqlalchemy import text
from ai import weights

MIN_WEIGHT = 5
MAX_WEIGHT = 50

# =====================================================
# TRADE COUNTER
# =====================================================

trade_counter = 0

# =====================================================
# LOAD SAVED WEIGHTS
# =====================================================

def load_weights():

    global weights

    with engine.begin() as conn:

        rows = conn.execute(text("""

        SELECT indicator, weight

        FROM ai_weights

        """)).fetchall()

    if rows:

        for r in rows:

            weights[r[0]] = float(r[1])

    return weights

# =====================================================
# SAVE WEIGHTS
# =====================================================

def save_weights():

    with engine.begin() as conn:

        for k, v in weights.items():

            conn.execute(text("""

            INSERT INTO ai_weights(
                indicator,
                weight
            )

            VALUES(
                :i,
                :w
            )

            ON CONFLICT(indicator)

            DO UPDATE SET

                weight = EXCLUDED.weight

            """), {

                "i": k,
                "w": v

            })

# =====================================================
# LEARNING ENGINE
# =====================================================

def learn_from_trade(signals, pnl):

    global weights
    global trade_counter

    try:

        trade_counter += 1

        for indicator, active in signals.items():

            if not active:
                continue

            # =====================================
            # PROFIT TRADE
            # =====================================

            if pnl > 0:

                weights[indicator] += 0.5

            # =====================================
            # LOSS TRADE
            # =====================================

            elif pnl < 0:

                weights[indicator] -= 0.5

        # =====================================
        # LIMITS
        # =====================================

        for k in weights:

            weights[k] = max(
                MIN_WEIGHT,
                min(MAX_WEIGHT, weights[k])
            )

        # =====================================
        # SAVE EVERY 10 TRADES
        # =====================================

        if trade_counter >= 10:

            save_weights()

            trade_counter = 0

    except Exception as e:

        print(e)
