from pathlib import Path
import yaml
from .rss import RSSAdapter

ROOT = Path(__file__).resolve().parents[2]

def load_sources(module):
    data = yaml.safe_load((ROOT / "config/sources.yaml").read_text(encoding="utf-8"))
    return data.get(module, {})

def build_rss_adapters(module):
    adapters = []
    for source in load_sources(module).get("rss", []):
        adapters.append(RSSAdapter(source["name"], source["url"]))
    return adapters
