from datetime import datetime, timezone

def provenance(source, source_type, field, value, confidence=1.0, status="observed"):
    return {
        "source": source,
        "source_type": source_type,
        "field": field,
        "value": value,
        "confidence": confidence,
        "status": status,
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }

def merge_field(existing, incoming):
    """Keep provenance rather than silently overwriting conflicting values."""
    values = []
    if existing:
        values.extend(existing if isinstance(existing, list) else [existing])
    if incoming:
        values.extend(incoming if isinstance(incoming, list) else [incoming])
    return values
