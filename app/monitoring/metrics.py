from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class PipelineMetrics:
    module: str
    discovered: int = 0
    ingested: int = 0
    verified: int = 0
    rejected: int = 0
    curated: int = 0
    duplicate_groups: int = 0
    source_errors: int = 0
    source_blocked: int = 0
    started_at: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return asdict(self)


def summarize_source_health(source_health: list[dict]) -> dict:
    counts = Counter(x.get("status", "unknown") for x in source_health)
    return dict(counts)
