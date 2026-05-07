weights={

"EMA":25,
"RSI":15,
"MACD":25,
"VWAP":20,
"VOLUME":15

}

def optimize_weights(win_rate):

    global weights

    if win_rate<50:

        weights["MACD"]+=2
        weights["EMA"]+=2

    return weights
