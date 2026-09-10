from rapidfuzz.fuzz import ratio
from app.normalize import canonical_key

def exact_duplicate(a, b):
    return canonical_key(a.get("name"), a.get("official_url"), a.get("company")) == canonical_key(
        b.get("name"), b.get("official_url"), b.get("company")
    )

def name_similarity(a, b):
    return ratio((a.get("name") or "").lower(), (b.get("name") or "").lower())

def likely_duplicate(a, b, threshold=92):
    if exact_duplicate(a, b):
        return True
    if a.get("official_url") and b.get("official_url"):
        if a["official_url"].split("?")[0].rstrip("/") == b["official_url"].split("?")[0].rstrip("/"):
            return True
    return name_similarity(a, b) >= threshold and (
        not a.get("company") or not b.get("company") or
        (a.get("company") or "").lower() == (b.get("company") or "").lower()
    )
