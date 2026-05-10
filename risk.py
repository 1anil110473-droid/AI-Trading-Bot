import math

# =========================================================
# BASIC POSITION SIZE ENGINE
# =========================================================

def position_size(

    capital,
    confidence,
    price

):

    try:

        risk_percent = 0.02

        allocation = (

            capital
            * risk_percent
            * (confidence / 100)

        )

        qty = int(allocation / price)

        qty = max(1, qty)

        return qty

    except:

        return 1

# =========================================================
# AI ADAPTIVE QUANTITY ENGINE
# =========================================================

def adaptive_quantity(

    capital,
    confidence,
    price,
    atr

):

    try:

        risk_per_trade = 0.02

        capital_risk = capital * risk_per_trade

        stop_distance = max(

            atr,
            price * 0.01

        )

        qty = capital_risk / stop_distance

        confidence_boost = confidence / 100

        qty = qty * confidence_boost

        qty = max(1, int(qty))

        return qty

    except:

        return 1

# =========================================================
# VOLATILITY RISK ENGINE
# =========================================================

def volatility_risk_multiplier(atr_percent):

    # =========================================
    # HIGH VOLATILITY
    # =========================================

    if atr_percent >= 4:

        return 0.5

    # =========================================
    # MEDIUM VOLATILITY
    # =========================================

    elif atr_percent >= 2:

        return 0.75

    # =========================================
    # LOW VOLATILITY
    # =========================================

    return 1.0

# =========================================================
# MAX EXPOSURE CHECK
# =========================================================

def exposure_ok(

    open_positions,
    max_positions=5

):

    return open_positions < max_positions
