def get_sector(stock):
    if "BANK" in stock or "SBIN" in stock:
        return "BANK"
    if stock in ["TCS.NS","INFY.NS","WIPRO.NS","COFORGE.NS"]:
        return "IT"
    if stock in ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS"]:
        return "PHARMA"
    if stock in ["TATASTEEL.NS","HINDZINC.NS","HINDCOPPER.NS"]:
        return "METAL"
    return "OTHER"

def sector_score(sector, signals):
    vals = signals.get(sector, [])
    if not vals:
        return 0
    return sum(vals)/len(vals)
