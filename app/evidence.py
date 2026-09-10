
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any
from urllib.parse import urlparse

from rapidfuzz.fuzz import token_set_ratio


@dataclass
class Evidence:
    field: str
    value: Any
    source_url: str
    evidence_text: str
    confidence: float
    method: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def evidence_for_field(
    field: str,
    value: Any,
    source_url: str,
    page_title: str = "",
    page_description: str = "",
    page_text: str = "",
) -> Evidence:
    """
    Conservative evidence builder.

    It never invents a value. Confidence only measures how strongly the
    supplied value is supported by the fetched page text.
    """
    value_text = clean_text(str(value))
    corpus = clean_text(" ".join([page_title, page_description, page_text]))

    if not value_text:
        return Evidence(field, value, source_url, "", 0.0, "empty")

    # Exact phrase is strongest.
    if value_text.lower() in corpus.lower():
        idx = corpus.lower().find(value_text.lower())
        snippet = corpus[max(0, idx - 180): idx + len(value_text) + 180]
        return Evidence(field, value, source_url, snippet, 1.0, "exact_phrase")

    # Token similarity is useful for company/product descriptions with minor
    # punctuation or formatting differences.
    ratio = token_set_ratio(value_text, corpus[:50_000]) / 100.0
    if ratio >= 0.80:
        return Evidence(field, value, source_url, corpus[:500], round(ratio, 3), "token_similarity")

    return Evidence(field, value, source_url, "", 0.0, "not_supported")


def source_domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")
