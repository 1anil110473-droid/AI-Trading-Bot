import math

# =========================================================
# AI ADAPTIVE QUANTITY ENGINE
# =========================================================

def adaptive_quantity(
    capital,
    confidence,
    price,
    atr
):

    risk_per_trade = 0.02

    capital_risk = capital * risk_per_trade

    stop_distance = max(atr, price * 0.01)

    qty = capital_risk / stop_distance

    confidence_boost = confidence / 100

    qty = qty * confidence_boost

    qty = max(1, int(qty))

    return qty
