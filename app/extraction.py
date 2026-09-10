
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse


PRICE_PATTERNS = [
    re.compile(r"\$\s?\d+(?:[.,]\d+)?(?:\s?/\s?(?:month|mo|year|yr))?", re.I),
    re.compile(r"€\s?\d+(?:[.,]\d+)?(?:\s?/\s?(?:month|mo|year|yr))?", re.I),
    re.compile(r"₹\s?\d+(?:[.,]\d+)?(?:\s?/\s?(?:month|mo|year|yr))?", re.I),
]


def _first_match(patterns, text: str) -> str | None:
    for pattern in patterns:
        match = pattern.search(text or "")
        if match:
            return match.group(0)
    return None


def extract_public_fields(candidate: dict[str, Any]) -> dict[str, Any]:
    """
    Conservative enrichment from already fetched public page content.
    Values are extracted only when explicit text patterns are present.
    """
    text = candidate.get("text", "") or ""
    title = candidate.get("title", "") or ""
    description = candidate.get("description", "") or ""

    result: dict[str, Any] = {}
    if title:
        result["page_title"] = title
    if description:
        result["page_description"] = description

    price = _first_match(PRICE_PATTERNS, text)
    if price:
        result["observed_price"] = price

    # Explicit API/GitHub signals, not assumptions.
    lowered = text.lower()
    if re.search(r"\bapi\b", lowered):
        result["api_mentioned"] = True
    if "github.com/" in lowered:
        result["github_mentioned"] = True

    result["source_domain"] = urlparse(candidate.get("final_url") or candidate.get("source_url") or "").netloc
    return result
