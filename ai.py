# =========================================================
# V54 SELF LEARNING AI ENGINE
# =========================================================

weights = {

    "EMA": 25,
    "RSI": 15,
    "MACD": 25,
    "VWAP": 20,
    "VOLUME": 15,
    "SUPPORT": 10,
    "RESISTANCE": 15,
    "BREAKOUT": 20

}

# =========================================================
# LIMITS
# =========================================================

MIN_WEIGHT = 5
MAX_WEIGHT = 50

# =========================================================
# SELF LEARNING ENGINE
# =========================================================

def optimize_weights(

    win_rate,
    avg_profit=0

):

    global weights

    try:

        # =============================================
        # HIGH WIN RATE
        # =============================================

        if win_rate >= 70:

            weights["EMA"] += 1
            weights["MACD"] += 1
            weights["BREAKOUT"] += 1

        # =============================================
        # LOW WIN RATE
        # =============================================

        elif win_rate <= 40:

            weights["RSI"] -= 1
            weights["VWAP"] -= 1

        # =============================================
        # HIGH PROFIT BOOST
        # =============================================

        if avg_profit > 1000:

            weights["BREAKOUT"] += 1

        # =============================================
        # LIMITS
        # =============================================

        for k in weights:

            weights[k] = max(
                MIN_WEIGHT,
                min(MAX_WEIGHT, weights[k])
            )

        return weights

    except:

        return weights

# =========================================================
# MARKET REGIME
# =========================================================

def market_regime(volatility):

    try:

        if volatility >= 3:
            return "HIGH_VOLATILITY"

        elif volatility >= 1.5:
            return "NORMAL_VOLATILITY"

        return "LOW_VOLATILITY"

    except:

        return "NORMAL_VOLATILITY"

# =========================================================
# ADAPTIVE CONFIDENCE BOOST
# =========================================================

def confidence_boost(

    base_score,
    trend,
    volatility,
    volume_spike=False,
    breakout=False

):

    try:

        score = base_score

        # =========================================
        # BULLISH BOOST
        # =========================================

        if trend == "BULLISH":

            score += 5

        # =========================================
        # VOLUME SPIKE BOOST
        # =========================================

        if volume_spike:

            score += 10

        # =========================================
        # BREAKOUT BOOST
        # =========================================

        if breakout:

            score += 10

        # =========================================
        # HIGH VOLATILITY PENALTY
        # =========================================

        if volatility >= 3:

            score -= 5

        return min(100, max(0, score))

    except:

        return base_score
