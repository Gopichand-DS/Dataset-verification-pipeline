import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT / "config" / "sources.yaml"

def load_sources(module=None):
    data = yaml.safe_load(SOURCE_FILE.read_text(encoding="utf-8"))
    if module:
        return data.get(module, {})
    return data

def discovery_sources(module):
    return load_sources(module).get("primary", [])

def secondary_sources(module):
    return load_sources(module).get("secondary", [])
