import json
import re
from urllib.parse import urlparse, urlunparse

try:
    import tldextract
except ImportError:  # dependency-free fallback for test/dev environments
    tldextract = None


def normalize_url(url):
    if not url:
        return None
    u = url.strip()
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    p = urlparse(u)
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/+$", "", p.path)
    return urlunparse(("https", host, path, "", "", ""))


def domain(url):
    if not url:
        return None
    if tldextract:
        x = tldextract.extract(url)
        return ".".join([v for v in (x.domain, x.suffix) if v])
    host = urlparse(url).netloc.lower().removeprefix("www.")
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def canonical_key(name, url=None, company=None):
    d = domain(normalize_url(url)) if url else ""
    n = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
    c = re.sub(r"[^a-z0-9]+", " ", (company or "").lower()).strip()
    return f"{d}|{n}|{c}"


def json_safe(obj):
    return json.dumps(obj, ensure_ascii=False, default=str)
