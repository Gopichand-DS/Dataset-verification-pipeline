import hashlib
from datetime import datetime, timezone
import feedparser
from rapidfuzz.fuzz import ratio

def fetch_rss(feed_url):
    feed = feedparser.parse(feed_url)
    articles = []
    for e in feed.entries:
        title = e.get("title", "").strip()
        link = e.get("link", "").strip()
        if not title or not link:
            continue
        articles.append({
            "title": title,
            "url": link,
            "published": e.get("published") or e.get("updated"),
            "summary": e.get("summary", ""),
            "source": feed.feed.get("title", ""),
        })
    return articles

def event_key(article):
    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in article["title"])
    return hashlib.sha256(" ".join(normalized.split()).encode()).hexdigest()

def similar_story(a, b, threshold=88):
    return ratio(a["title"].lower(), b["title"].lower()) >= threshold

def rank_news(article, factors):
    # Caller supplies 0-100 factor values using config/scoring.yaml.
    weights = {
        "source_credibility": 25, "coverage": 15, "company_importance": 15,
        "impact": 20, "trending": 5, "recency": 10, "relevance": 10
    }
    return round(sum(factors.get(k, 0) * w for k, w in weights.items()) / 100, 2)
