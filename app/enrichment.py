from datetime import datetime, timezone

def empty_enrichment():
    return {
        "fields": {},
        "sources": [],
        "enriched_at": datetime.now(timezone.utc).isoformat(),
        "notes": []
    }

def add_field(enrichment, field, value, source, confidence="medium"):
    if value in (None, "", []):
        return enrichment
    enrichment["fields"][field] = {
        "value": value,
        "source": source,
        "confidence": confidence
    }
    if source not in enrichment["sources"]:
        enrichment["sources"].append(source)
    return enrichment
