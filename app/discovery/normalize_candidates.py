import re
from app.normalize import canonical_key, normalize_url

def clean(value):
    if value is None: return ""
    if isinstance(value, str): return re.sub(r"\s+", " ", value).strip()
    return value

def normalize_candidate(item: dict, source: dict) -> dict:
    row={k:clean(v) for k,v in dict(item).items()}
    name=row.get("name") or row.get("title") or row.get("tool_name") or row.get("model_name") or row.get("company_name")
    url=row.get("official_url") or row.get("website") or row.get("url")
    company=row.get("company") or row.get("manufacturer") or row.get("provider") or ""
    if url: url=normalize_url(url)
    prior=row.get("discovery_sources") or []
    if isinstance(prior,str): prior=[prior]
    row.update({
        "name":clean(name),"official_url":url or "","company":clean(company),
        "discovery_source":source.get("name",""),
        "discovery_source_url":source.get("url",""),
        "discovery_sources":list(dict.fromkeys([*prior,source.get("name",""),source.get("url","")])),
        "verification_status":"unverified"
    })
    return row

def candidate_key(item: dict) -> str:
    return canonical_key(item.get("name"), item.get("official_url") or item.get("url"), item.get("company"))
