from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
import html
from typing import Any
from urllib.parse import urlparse

import requests


@dataclass
class VerificationResult:
    url: str
    status: str
    http_status: int | None = None
    final_url: str = ""
    title: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    checked_at: str = ""

    def __post_init__(self):
        if not self.checked_at:
            self.checked_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return self.__dict__.copy()


def verify_official_url(url: str, timeout: int = 15) -> VerificationResult:
    """Lightweight official URL gate.

    This proves reachability/page evidence only. It does NOT prove every
    product field. Field-level verification must still be performed by the
    normal verification stage.
    """
    if not url:
        return VerificationResult("", "missing_url", error="No URL supplied")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return VerificationResult(url, "invalid_url", error="Invalid HTTP(S) URL")

    headers = {
        "User-Agent": "AIOrbit-Curator/5.0 (+verification)",
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        r = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        status = "verified" if 200 <= r.status_code < 400 else (
            "blocked_or_rate_limited" if r.status_code in {401,403,429} else "unreachable"
        )
        title = ""
        if "text/html" in r.headers.get("content-type","").lower():
            m = re.search(r"<title[^>]*>(.*?)</title>", r.text[:200000], re.I | re.S)
            if m:
                title = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()[:500]
        return VerificationResult(
            url=url, status=status, http_status=r.status_code,
            final_url=r.url, title=title,
            evidence={"content_type": r.headers.get("content-type",""), "bytes": len(r.content), "title": title, "description": (re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', r.text[:200000], re.I) or [None, ""])[1], "text": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text[:200000])).strip()[:200000]}
        )
    except requests.RequestException as exc:
        return VerificationResult(url, "error", error=str(exc))
