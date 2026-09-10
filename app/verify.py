import json
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from app.config import REQUEST_TIMEOUT
from app.normalize import normalize_url

HEADERS = {"User-Agent": "AIOrbitCurator/1.0 verification"}

def fetch_official_page(url):
    if not url:
        return {"verified": False, "status": "missing_official_url", "final_url": None,
                "title": "", "description": "", "text": "", "http_status": None, "error": None}
    url = normalize_url(url)
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        meta = soup.find("meta", attrs={"name": "description"})
        description = meta.get("content", "").strip() if meta else ""
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(soup.get_text(" ", strip=True).split())
        return {"verified": r.ok, "status": "active" if r.ok else f"http_{r.status_code}",
                "final_url": r.url, "title": title[:1000], "description": description[:3000],
                "text": text[:30000], "http_status": r.status_code, "error": None}
    except requests.RequestException as e:
        return {"verified": False, "status": "request_error", "final_url": url,
                "title": "", "description": "", "text": "", "http_status": None, "error": str(e)}

def build_verification(record, page):
    raw = json.loads(record.raw_json or "{}")
    official_url = page.get("final_url") or record.official_url
    haystack = (page.get("title","") + " " + page.get("description","")).lower()
    checks = {
        "name": {
            "result": "verified" if page.get("verified") and record.name.lower() in haystack else "unverifiable",
            "ingested": record.name,
            "verified": page.get("title") or None
        }
    }
    supplied = raw.get("description") or raw.get("overview")
    if supplied:
        checks["description"] = {
            "result": "verified" if page.get("description") and
                      any(w.lower() in page["description"].lower() for w in str(supplied).split()[:8])
                      else "unverifiable",
            "ingested": str(supplied),
            "verified": page.get("description") or None
        }
    return {
        "verified": bool(page.get("verified")),
        "status": page.get("status"),
        "official_url": official_url,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "evidence": {"http_status": page.get("http_status"), "source": official_url, "error": page.get("error")}
    }
