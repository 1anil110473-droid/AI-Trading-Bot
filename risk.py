def position_size(capital,confidence,price):

    risk_percent=0.02

    allocation=capital*risk_percent*(confidence/100)

    qty=max(1,int(allocation/price))

    return qty
