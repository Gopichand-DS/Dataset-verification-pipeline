# Production scheduler entry point.
# Add configured RSS/API sources and call app.news_pipeline.fetch_rss().
# Then normalize, cluster by event, verify significant stories, rank, and persist top 20-30.

from app.config import ROOT
print("AIOrbit daily news worker scaffold. Configure source adapters before production use.")
