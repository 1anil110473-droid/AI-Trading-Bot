from db import engine
from sqlalchemy import text
from ai import weights

MIN_WEIGHT = 5
MAX_WEIGHT = 50

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

    try:

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

        save_weights()

    except Exception as e:

        print(e)
