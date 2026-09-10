from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

@dataclass
class SourceHealth:
    source_name: str
    url: str
    status: str
    http_status: Optional[int] = None
    error: Optional[str] = None
    candidate_count: int = 0
    checked_at: str = ""
    def __post_init__(self):
        if not self.checked_at:
            self.checked_at = datetime.now(timezone.utc).isoformat()
    def to_dict(self): return asdict(self)

def classify_http(status_code: int | None) -> str:
    if status_code is None: return "error"
    if 200 <= status_code < 300: return "ok"
    if status_code in {401,403,429}: return "blocked_or_rate_limited"
    if 400 <= status_code < 500: return "client_error"
    if 500 <= status_code < 600: return "server_error"
    return "unexpected"
