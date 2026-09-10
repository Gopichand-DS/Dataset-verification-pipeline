
from __future__ import annotations

from datetime import datetime, timezone
from time import sleep
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .base import SourceAdapter


class WebPageAdapter(SourceAdapter):
    """Fetch publicly accessible HTML pages with bounded retries."""

    name = "webpage"

    def __init__(
        self,
        timeout: int = 20,
        user_agent: str = "AIOrbitCurator/1.0",
        retries: int = 3,
        backoff_seconds: float = 1.0,
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.retries = max(1, retries)
        self.backoff_seconds = backoff_seconds

    def fetch(self, url: str) -> requests.Response:
        last_response = None
        last_error = None

        for attempt in range(self.retries):
            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml",
                    },
                    allow_redirects=True,
                )

            # Do not raise on access-control responses.
            # Return them so the pipeline can record the failure.
                if response.status_code in {401, 403, 429}:
                    return response

                response.raise_for_status()
                return response

            except requests.RequestException as exc:
                last_error = exc

                if attempt < self.retries - 1:
                    sleep(self.backoff_seconds * (2 ** attempt))

        if last_error:
            raise last_error

        raise RuntimeError(f"Unable to fetch {url}")
    
    def discover(self, url: str, **kwargs: Any) -> list[dict[str, Any]]:
        response = self.fetch(url)
        if response.status_code in {401, 403, 429}:
            return [{
                "source_url": url,
                "final_url": response.url,
                "status_code": response.status_code,
                "access_status": "blocked_or_rate_limited",
                "title": "",
                "description": "",
                "text": "",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "discovery_type": "webpage",
            }]
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()

        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        description = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            description = meta.get("content", "") or ""

        canonical = soup.find("link", attrs={"rel": "canonical"})
        canonical_url = (
            urljoin(response.url, canonical.get("href"))
            if canonical and canonical.get("href")
            else response.url
        )

        text = soup.get_text(" ", strip=True)
        links = []
        for a in soup.find_all("a", href=True):
            links.append(urljoin(response.url, a.get("href", "").strip()))
        return [{
            "source_url": url,
            "final_url": response.url,
            "canonical_url": canonical_url,
            "title": title,
            "description": description,
            "text": text[:200_000],
            "links": list(dict.fromkeys(links))[:500],
            "status_code": response.status_code,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "discovery_type": "webpage",
        }]
