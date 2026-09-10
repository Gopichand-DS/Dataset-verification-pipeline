from .semantic_dedupe import is_duplicate

def cluster_articles(articles):
    clusters = []
    for article in articles:
        placed = False
        for cluster in clusters:
            if any(is_duplicate(article, other, threshold=0.88) for other in cluster):
                cluster.append(article)
                placed = True
                break
        if not placed:
            clusters.append([article])
    return clusters

def select_best_article(cluster):
    # Prefer official sources, then richer articles. Production should use
    # configurable source-quality scores and entity/event extraction.
    def key(a):
        source = str(a.get("source", "")).lower()
        official = any(x in source for x in ("openai", "google", "microsoft", "nvidia", "anthropic"))
        return (1 if official else 0, len(str(a.get("summary", ""))))
    return sorted(cluster, key=key, reverse=True)[0]
