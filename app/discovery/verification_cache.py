from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


class VerificationCache:
    def __init__(self, path="data/verification_cache.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self):
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _key(self, url):
        return hashlib.sha256(url.strip().lower().encode()).hexdigest()

    def get(self, url, max_age_hours=24):
        item = self.data.get(self._key(url))
        if not item:
            return None
        try:
            checked = datetime.fromisoformat(item["checked_at"])
            age = (datetime.now(timezone.utc) - checked).total_seconds() / 3600
            if age <= max_age_hours:
                return item
        except Exception:
            pass
        return None

    def put(self, url, result):
        item = dict(result)
        item["checked_at"] = datetime.now(timezone.utc).isoformat()
        self.data[self._key(url)] = item
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        return item
