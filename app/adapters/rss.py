import feedparser
from .base import SourceAdapter

class RSSAdapter(SourceAdapter):
    source_type = "discovery"

    def __init__(self, name, feed_url):
        self.name = name
        self.feed_url = feed_url

    def discover(self):
        feed = feedparser.parse(self.feed_url)
        for entry in feed.entries:
            yield {
                "name": entry.get("title", "").strip(),
                "url": entry.get("link", "").strip(),
                "description": entry.get("summary", ""),
                "published": entry.get("published") or entry.get("updated"),
                "source": self.name,
                "discovery_type": "rss",
            }
