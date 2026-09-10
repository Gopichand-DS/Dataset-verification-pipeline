from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class SourceHealth:
    source: str
    success: bool
    status: str
    checked_at: str

def record(source, success, status):
    return SourceHealth(
        source=source,
        success=success,
        status=status,
        checked_at=datetime.now(timezone.utc).isoformat()
    )
