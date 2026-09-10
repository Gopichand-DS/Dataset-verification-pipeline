from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from rapidfuzz.fuzz import token_set_ratio, WRatio

PAGE_HINTS = {
    "pricing": ("pricing", "plans", "plan", "cost"),
    "login": ("login", "log in", "signin", "sign in", "account"),
    "signup": ("sign up", "signup", "get started", "register"),
    "api": ("api", "developer", "developers", "docs", "documentation"),
    "about": ("about", "company"),
    "terms": ("terms", "legal"),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_tool_id(name: str, official_url: str) -> str:
    """Stable deterministic ID generated from normalized product identity."""
    parsed = urlparse(official_url or "")
    domain = parsed.netloc.lower().split(":", 1)[0].removeprefix("www.")
    seed = f"{domain}|{re.sub(r'[^a-z0-9]+', '-', (name or '').lower()).strip('-')}"
    return "tool_" + sha256(seed.encode("utf-8")).hexdigest()[:20]


def _same_site(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower().removeprefix("www.") == urlparse(b).netloc.lower().removeprefix("www.")


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _page(url: str, timeout: int = 15) -> dict[str, Any]:
    r = requests.get(url, timeout=timeout, headers={
        "User-Agent": "AIOrbit-Curator/6.7 (+verification)",
        "Accept": "text/html,application/xhtml+xml",
    }, allow_redirects=True)
    soup = BeautifulSoup(r.text if "html" in r.headers.get("content-type", "").lower() else "", "html.parser")
    title = _clean(soup.title.get_text(" ", strip=True) if soup.title else "")
    description = ""
    meta = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    if meta:
        description = _clean(meta.get("content", ""))
    og_image = ""
    og = soup.find("meta", attrs={"property": "og:image"})
    if og:
        og_image = urljoin(r.url, og.get("content", ""))
    text = _clean(soup.get_text(" ", strip=True))[:250000]
    links = []
    for a in soup.find_all("a", href=True):
        href = urljoin(r.url, a.get("href", ""))
        if href.startswith(("http://", "https://")):
            links.append({"url": href, "text": _clean(a.get_text(" ", strip=True))[:200]})
    return {"url": url, "final_url": r.url, "status_code": r.status_code, "title": title,
            "description": description, "text": text, "links": links, "logo_url": og_image,
            "checked_at": _now()}


def _choose_links(home: dict[str, Any]) -> dict[str, str]:
    found: dict[str, str] = {}
    for link in home.get("links", []):
        u, label = link.get("url", ""), (link.get("text", "") or "").lower()
        hay = f"{label} {u.lower()}"
        if not _same_site(home.get("final_url", home.get("url", "")), u):
            continue
        for kind, hints in PAGE_HINTS.items():
            if kind not in found and any(h in hay for h in hints):
                found[kind] = u
    return found


def _find_external(home: dict[str, Any], host_terms: tuple[str, ...]) -> str:
    for link in home.get("links", []):
        u = link.get("url", "")
        if any(t in u.lower() for t in host_terms):
            return u
    return ""


def _pricing(text: str) -> dict[str, Any]:
    low = text.lower()
    free = bool(re.search(r"\bfree\b", low))
    paid = bool(re.search(r"\b(?:pro|premium|paid|business|enterprise|starter)\b", low))
    amounts = sorted(set(re.findall(r"(?:[$€£]|usd\s*)\s?\d+(?:[.,]\d+)?(?:\s*/\s*(?:month|mo|year|yr|week|user))?", text, re.I)))
    model = "freemium" if free and paid else ("paid" if paid else ("free" if free else "not publicly disclosed"))
    return {"model": model, "amounts": amounts[:20], "has_free": free, "has_paid": paid}


def _access(home_text: str, login_text: str = "", signup_text: str = "") -> dict[str, Any]:
    corpus = " ".join((home_text, login_text, signup_text)).lower()
    has_login = bool(re.search(r"\b(sign in|signin|log in|login)\b", corpus))
    has_signup = bool(re.search(r"\b(sign up|signup|register|create an account)\b", corpus))
    if has_login or has_signup:
        return {"account_required": "likely", "access_method": "account/login", "evidence": "Account/login language found on official pages."}
    return {"account_required": "not publicly established", "access_method": "not publicly disclosed", "evidence": "No explicit account requirement found on crawled official pages."}


def _company(text: str, title: str = "") -> str:
    patterns = [
        r"(?:a product of|by|from)\s+([A-Z][A-Za-z0-9&.,' -]{2,80})",
        r"©\s*(?:20\d\d\s*)?([A-Z][A-Za-z0-9&.,' -]{2,80})",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return _clean(m.group(1)).strip(" .|-")
    return ""


def _launch_date(*texts: str) -> str:
    corpus = " ".join(texts)
    # Prefer explicit launch/founded/released phrases; do not invent exact dates.
    m = re.search(r"(?:launched|launch|released|founded|established)\D{0,50}(20\d{2}(?:[-/]\d{1,2}(?:[-/]\d{1,2})?)?)", corpus, re.I)
    return m.group(1) if m else ""



def _section_items(text: str, headings: tuple[str, ...], max_items: int = 8) -> list[str]:
    """Extract short, field-specific claims from nearby official-page text.

    This intentionally looks for explicit section headings/phrasing instead of
    recycling the product description for every field.
    """
    out: list[str] = []
    for heading in headings:
        pattern = re.compile(
            rf"(?:^|[.!?]\s|\n)\s*(?:{re.escape(heading)})\s*[:\-]?\s*(.{{0,900}})",
            re.I,
        )
        for m in pattern.finditer(text):
            chunk = m.group(1)
            # Stop at the next likely section heading.
            chunk = re.split(
                r"\s+(?:features?|benefits?|advantages?|pros?|cons?|limitations?|pricing|plans?|faq|use cases?|capabilities?)\s*[:\-]",
                chunk,
                maxsplit=1,
                flags=re.I,
            )[0]
            parts = re.split(r"[•·|]|\s+\d+[.)]\s+|\n+", chunk)
            for part in parts:
                part = _clean(part).strip(" :-")
                if 12 <= len(part) <= 220 and part.lower() not in {x.lower() for x in out}:
                    out.append(part)
                if len(out) >= max_items:
                    return out
    return out


def _features(text: str) -> list[str]:
    items = _section_items(
        text,
        ("features", "key features", "capabilities", "what you can do", "features include"),
        10,
    )
    if not items:
        # Fallback only to explicit capability sentences; never use the whole description.
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            low = sentence.lower()
            if any(x in low for x in ("lets you", "allows you to", "can generate", "can create", "supports ", "provides ")):
                sentence = _clean(sentence)
                if 20 <= len(sentence) <= 220:
                    items.append(sentence)
            if len(items) >= 8:
                break
    return list(dict.fromkeys(items))[:10]


def _benefits(text: str) -> list[str]:
    return _section_items(
        text,
        ("benefits", "advantages", "why use", "why choose", "built for", "benefit"),
        8,
    )


def _limitations(text: str) -> list[str]:
    return _section_items(
        text,
        ("limitations", "limitations include", "restrictions", "requirements", "constraints", "disadvantages", "cons"),
        8,
    )


def _root_tokens(value: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    roots = set()
    for token in tokens:
        if len(token) > 5 and token.endswith("ing"):
            token = token[:-3]
        elif len(token) > 4 and token.endswith("ed"):
            token = token[:-2]
        elif len(token) > 4 and token.endswith("s"):
            token = token[:-1]
        roots.add(token)
    return roots


def _text_similarity(a: Any, b: Any) -> float:
    aa = _clean(str(a or ""))
    bb = _clean(str(b or ""))
    if not aa or not bb:
        return 0.0
    fuzzy = max(token_set_ratio(aa, bb), WRatio(aa, bb)) / 100.0
    ta, tb = _root_tokens(aa), _root_tokens(bb)
    overlap = (len(ta & tb) / max(1, min(len(ta), len(tb)))) if ta and tb else 0.0
    return max(fuzzy, overlap)


def _cross_field_duplicate(a: Any, b: Any, threshold: float = 0.82) -> bool:
    if isinstance(a, list): a = " ".join(map(str, a))
    if isinstance(b, list): b = " ".join(map(str, b))
    return _text_similarity(a, b) >= threshold


def _pros_cons(record: dict[str, Any], pages: dict[str, dict[str, Any]], pricing: dict[str, Any], access: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Extract distinct, evidence-backed strengths and limitations.

    Pros/cons are never copied from the description/features. If the official
    pages do not establish a real strength or limitation, the result is empty.
    """
    all_text = " ".join(p.get("text", "") for p in pages.values())
    pros: list[str] = _benefits(all_text)
    cons: list[str] = _limitations(all_text)

    # Add concrete official evidence only when it represents a distinct claim.
    if pricing.get("has_free"):
        pros.append("Official site documents a free access option.")
    if pricing.get("has_paid") and pricing.get("amounts"):
        cons.append("Official site documents paid pricing for at least one plan or tier.")
    if access.get("account_required") == "likely":
        cons.append("Official pages indicate that an account or login is required for at least part of the product flow.")

    def unique(items: list[str]) -> list[str]:
        result: list[str] = []
        for item in items:
            item = _clean(item)
            if not item:
                continue
            if any(_cross_field_duplicate(item, existing, 0.86) for existing in result):
                continue
            result.append(item)
        return result[:6]

    return unique(pros), unique(cons)

def _valid_http_url(url: str) -> bool:
    try:
        p = urlparse(url or "")
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")


def _extract_list(text: str, labels: tuple[str, ...], max_items: int = 12) -> list[str]:
    low = text.lower()
    out: list[str] = []
    for label in labels:
        for m in re.finditer(re.escape(label), low):
            chunk = text[m.end():m.end()+700]
            chunk = re.split(r"(?:\n|\.|;|\b(?:features?|pricing|faq|reviews?)\b)", chunk, maxsplit=1, flags=re.I)[0]
            parts = re.split(r"[•|·]|\s+-\s+|\s+\*\s+", chunk)
            for part in parts:
                part = _clean(part).strip(":-")
                if 4 <= len(part) <= 180 and part.lower() not in {x.lower() for x in out}:
                    out.append(part)
                if len(out) >= max_items:
                    return out
    return out


def _target_users(text: str) -> list[str]:
    terms = ("for developers", "for teams", "for businesses", "for marketers", "for students", "for educators", "for creators", "for researchers", "for enterprises", "for professionals")
    found = []
    low = text.lower()
    for term in terms:
        if term in low:
            found.append(term.replace("for ", "").title())
    return list(dict.fromkeys(found))


def _compatibility(text: str) -> list[str]:
    low = text.lower()
    out=[]
    checks={"Browser/Web": ("web app", "browser", "web browser", "online"), "Windows": ("windows",), "macOS": ("macos", "mac os"), "Linux": ("linux",), "iOS": ("ios", "iphone", "ipad"), "Android": ("android",), "Desktop": ("desktop app", "desktop application"), "Mobile": ("mobile app", "mobile application")}
    for name, terms in checks.items():
        if any(t in low for t in terms): out.append(name)
    return out


def _pricing_tiers(text: str) -> list[dict[str, str]]:
    tiers=[]
    # Capture common tier headings followed by a nearby price. This is deliberately conservative.
    for m in re.finditer(r"\b(Free|Basic|Starter|Pro|Premium|Team|Business|Enterprise|Plus|Standard|Ultimate)\b", text, re.I):
        name=_clean(m.group(1))
        chunk=text[m.end():m.end()+180]
        price=re.search(r"(?:[$€£]|USD\s*)\s?\d+(?:[.,]\d+)?(?:\s*/\s*(?:month|mo|year|yr|week|user))?", chunk, re.I)
        tiers.append({"name":name, "price":price.group(0) if price else ""})
    seen=set(); result=[]
    for x in tiers:
        k=(x["name"].lower(),x["price"].lower())
        if k not in seen: seen.add(k); result.append(x)
    return result[:12]


def _recent_update(*texts: str) -> str:
    corpus=" ".join(texts)
    patterns=(r"(?:last updated|updated on|updated)\D{0,30}(20\d{2}[-/]\d{1,2}(?:[-/]\d{1,2})?)", r"(?:release|released|version)\D{0,40}(20\d{2}[-/]\d{1,2}(?:[-/]\d{1,2})?)")
    for pattern in patterns:
        m=re.search(pattern, corpus, re.I)
        if m: return m.group(1)
    return ""


def _performance_score(record: dict[str, Any], evidence: dict[str, Any]) -> float:
    """Evidence-quality score, not a fabricated benchmark/performance claim."""
    checks=[
        bool(evidence.get("identity",{}).get("status")=="verified"),
        bool(record.get("features")), bool(record.get("description")),
        bool(record.get("pricingModel") or record.get("pricingEvidence")),
        bool(record.get("useCases") or record.get("targetUsers")),
        bool(record.get("aiorbit_category") or record.get("toolCategories")),
    ]
    return round(100*sum(checks)/len(checks), 1)

def enrich_tool(record: dict[str, Any], max_pages: int = 8) -> dict[str, Any]:
    """Independently inspect an official product site and enrich tool facts conservatively."""
    url = record.get("official_url") or record.get("websiteUrl") or ""
    if not url:
        return record
    home = _page(url)
    pages = {"home": home}
    selected = _choose_links(home)
    for kind, page_url in list(selected.items())[: max(0, max_pages - 1)]:
        try:
            pages[kind] = _page(page_url)
        except requests.RequestException:
            continue

    all_text = " ".join(p.get("text", "") for p in pages.values())
    home_text = home.get("text", "")
    pricing = _pricing(pages.get("pricing", {}).get("text", "") or all_text)
    pricing["tiers"] = _pricing_tiers(pages.get("pricing", {}).get("text", "") or all_text)
    access = _access(home_text, pages.get("login", {}).get("text", ""), pages.get("signup", {}).get("text", ""))
    links = [x.get("url", "") for p in pages.values() for x in p.get("links", []) if _valid_http_url(x.get("url", ""))]
    github = next((u for u in links if "github.com/" in u.lower()), "")
    linkedin = next((u for u in links if "linkedin.com/" in u.lower()), "")
    twitter = next((u for u in links if "twitter.com/" in u.lower() or "x.com/" in u.lower()), "")
    api = selected.get("api", "")

    final_url = home.get("final_url") or url
    record["official_url"] = final_url
    record["websiteVerification"] = {
        "input_url": url, "final_url": final_url,
        "valid_http_url": _valid_http_url(final_url),
        "status_code": home.get("status_code"),
        "same_product_domain": _same_site(url, final_url),
        "identity_title": home.get("title", ""),
    }

    # Official logo evidence. Prefer og:image; only mark it as a logo when the
    # metadata/alt text identifies it as branding, otherwise keep it as candidate.
    logo = home.get("logo_url", "")
    if not record.get("logoUrl") and logo:
        record["logoUrl"] = logo
    record["logoVerification"] = {
        "url": record.get("logoUrl", ""),
        "valid_url": _valid_http_url(str(record.get("logoUrl", ""))),
        "official_page_reference": bool(record.get("logoUrl", "")) and str(record.get("logoUrl", "")).rstrip("/").lower() in {u.rstrip("/").lower() for u in links + [logo]},
        "source": "official_page_metadata",
        "note": "URL and official-page reference checked; visual identity match is not claimed without image-level inspection."
    }

    record.setdefault("slug", _slug(str(record.get("name", ""))))
    extracted_features = _features(all_text)
    existing_features = record.get("features")
    if not existing_features or _cross_field_duplicate(existing_features, record.get("description", ""), 0.88):
        record["features"] = extracted_features
    else:
        record["features"] = existing_features
    record.setdefault("targetUsers", _target_users(all_text))
    record.setdefault("compatibility", _compatibility(all_text))
    record.setdefault("useCases", _extract_list(all_text, ("use cases", "use case", "works for", "ideal for")))
    record.setdefault("toolCategories", [])

    if not record.get("githubUrl") and github: record["githubUrl"] = github
    if not record.get("linkedInUrl") and linkedin: record["linkedInUrl"] = linkedin
    if not record.get("twitterUrl") and twitter: record["twitterUrl"] = twitter
    if not record.get("apiDocsUrl") and api: record["apiDocsUrl"] = api
    if not record.get("hasApi"): record["hasApi"] = bool(api or re.search(r"\bAPI\b", all_text, re.I))
    # Do not infer open-source from a GitHub link alone; require explicit wording.
    if not record.get("isOpenSource"):
        record["isOpenSource"] = bool(re.search(r"\bopen[- ]source\b", all_text, re.I))

    if not record.get("description"):
        record["description"] = home.get("description") or home.get("title", "")
    if not record.get("pricingModel") and pricing["model"] != "not publicly disclosed": record["pricingModel"] = pricing["model"]
    if not record.get("pricingAmount") and pricing["amounts"]: record["pricingAmount"] = ", ".join(pricing["amounts"][:8])
    if not record.get("billingFrequency"):
        joined=" ".join(pricing["amounts"]).lower()
        record["billingFrequency"] = next((x for x in ("month", "year", "week", "user") if f"/{x}" in joined), "")
    if not record.get("pricingTiers"): record["pricingTiers"] = pricing["tiers"]

    company = record.get("releasedBy") or record.get("company") or _company(all_text, home.get("title", ""))
    if company:
        record["releasedBy"] = company; record["company"] = company
    record["companyVerification"] = {"company": company, "source": "official_site" if company else "", "status": "verified" if company else "unsupported"}

    launch = record.get("launchDate") or record.get("releaseDate") or _launch_date(all_text)
    if launch: record["launchDate"] = launch; record["releaseDate"] = launch
    recent = record.get("recentlyUpdated") or _recent_update(all_text)
    if recent: record["recentlyUpdated"] = recent

    pros, cons = _pros_cons(record, pages, pricing, access)
    existing_pros = record.get("pros")
    existing_cons = record.get("cons")
    # If source/input content is duplicated across features/pros/cons, prefer
    # field-specific official extraction. Never manufacture a replacement.
    if not existing_pros or _cross_field_duplicate(existing_pros, record.get("features", []), 0.82) or _cross_field_duplicate(existing_pros, record.get("cons", []), 0.82):
        record["pros"] = pros
    if not existing_cons or _cross_field_duplicate(existing_cons, record.get("features", []), 0.82) or _cross_field_duplicate(existing_cons, record.get("pros", []), 0.82):
        record["cons"] = cons
    # Final cross-field guard. If two fields remain near-identical after extraction,
    # keep the more evidence-specific field and blank the weaker one.
    if _cross_field_duplicate(record.get("features", []), record.get("pros", []), 0.90):
        record["pros"] = [] if not pros else pros
    if _cross_field_duplicate(record.get("features", []), record.get("cons", []), 0.90):
        record["cons"] = [] if not cons else cons
    if _cross_field_duplicate(record.get("pros", []), record.get("cons", []), 0.90):
        record["cons"] = cons if not _cross_field_duplicate(pros, cons, 0.90) else []
    record["field_separation"] = {
        "features_source": "official_site_field_specific_extraction",
        "pros_source": "official_site_benefits_and_explicit_strength_evidence",
        "cons_source": "official_site_limitations_and_explicit_restriction_evidence",
        "duplicate_guard": "token_set_similarity",
    }
    record["accountAccess"] = access
    record["pricingEvidence"] = pricing
    record["crawledOfficialPages"] = [{"type": k, "url": p.get("final_url") or p.get("url"), "status_code": p.get("status_code"), "title": p.get("title", "")} for k,p in pages.items()]
    record["officialSourceText"] = all_text[:250000]
    record["officialLinks"] = links[:500]
    record["canonical_id"] = canonical_tool_id(str(record.get("name", "")), str(final_url))
    record["lastVerifiedAt"] = _now()
    record["categoryCount"] = len(record.get("aiorbit_categories") or record.get("toolCategories") or [])
    record["performanceScore"] = record.get("performanceScore") or _performance_score(record, {"identity":{"status":"verified" if home.get("status_code",0) < 400 else "unverified"}})
    return record
