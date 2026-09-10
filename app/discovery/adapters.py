from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urljoin

import requests


@dataclass
class AdapterResult:
    source: str
    url: str
    status: str
    status_code: int | None
    candidates: list[dict[str, Any]]
    error: str | None = None


class DiscoveryAdapter:
    """Base adapter. Adapters produce candidates, never verified facts."""

    def discover(self, source: dict) -> AdapterResult:
        raise NotImplementedError


class JSONFeedAdapter(DiscoveryAdapter):
    """Adapter for public JSON endpoints containing a list of entities."""

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def discover(self, source: dict) -> AdapterResult:
        url = source["url"]
        try:
            r = requests.get(
                url, timeout=self.timeout,
                headers={"User-Agent": "AIOrbit-Curator/6.0", "Accept": "application/json"}
            )
            if r.status_code in {401, 403, 429}:
                return AdapterResult(source["name"], url, "blocked_or_rate_limited",
                                     r.status_code, [])
            r.raise_for_status()
            payload = r.json()
            rows = payload if isinstance(payload, list) else (
                payload.get(source.get("items_key", "items"), [])
                if isinstance(payload, dict) else []
            )
            candidates = []
            for row in rows:
                if isinstance(row, dict):
                    candidates.append(dict(row))
            return AdapterResult(source["name"], url, "ok", r.status_code, candidates)
        except Exception as exc:
            return AdapterResult(source["name"], url, "error", None, [], str(exc))


class SitemapAdapter(DiscoveryAdapter):
    """Extract candidate URLs from a public XML sitemap."""

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def discover(self, source: dict) -> AdapterResult:
        url = source["url"]
        try:
            r = requests.get(
                url, timeout=self.timeout,
                headers={"User-Agent": "AIOrbit-Curator/6.0", "Accept": "application/xml,text/xml"}
            )
            if r.status_code in {401, 403, 429}:
                return AdapterResult(source["name"], url, "blocked_or_rate_limited",
                                     r.status_code, [])
            r.raise_for_status()
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.content)
            candidates = []
            for loc in root.iter():
                if loc.tag.lower().endswith("loc") and loc.text:
                    candidates.append({
                        "name": loc.text.rstrip("/").split("/")[-1].replace("-", " ").strip(),
                        "official_url": urljoin(url, loc.text.strip()),
                        "discovery_type": "sitemap"
                    })
            return AdapterResult(source["name"], url, "ok", r.status_code, candidates)
        except Exception as exc:
            return AdapterResult(source["name"], url, "error", None, [], str(exc))
