import os, requests

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_sentiment(stock):
    try:
        if not NEWS_API_KEY:
            return 0  # fallback safe

        url = f"https://newsapi.org/v2/everything?q={stock}&apiKey={NEWS_API_KEY}&pageSize=5"
        res = requests.get(url, timeout=5).json()

        articles = res.get("articles", [])
        if not articles:
            return 0

        score = 0

        for a in articles:
            text = (a.get("title","") + a.get("description","")).lower()

            if any(x in text for x in ["profit","growth","bull","up","gain"]):
                score += 1
            elif any(x in text for x in ["loss","down","fall","bear","crash"]):
                score -= 1

        return score / len(articles)

    except:
        return 0
