from app.news_pipeline import similar_story

NEWS_WEIGHTS = {
    "source_credibility": 25,
    "coverage": 15,
    "company_importance": 15,
    "impact": 20,
    "trending": 5,
    "recency": 10,
    "relevance": 10,
}

def score_story(factors):
    return round(sum(factors.get(k, 0) * w for k, w in NEWS_WEIGHTS.items()) / 100, 2)

def cluster_stories(articles):
    clusters = []
    for article in articles:
        placed = False
        for cluster in clusters:
            if any(similar_story(article, x) for x in cluster):
                cluster.append(article)
                placed = True
                break
        if not placed:
            clusters.append([article])
    return clusters

def representative(cluster):
    # Source-specific credibility should be supplied by the caller.
    return max(cluster, key=lambda x: len(x.get("summary", "")))
