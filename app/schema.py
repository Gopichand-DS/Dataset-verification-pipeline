from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

def now():
    return datetime.now(timezone.utc)

class Candidate(BaseModel):
    module: str
    name: str
    official_url: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)

class Verification(BaseModel):
    candidate_key: str
    verified: bool
    official_url: Optional[str] = None
    status: str = "unknown"
    evidence: Dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=now)
    notes: Optional[str] = None

class Score(BaseModel):
    candidate_key: str
    overall: float
    factors: Dict[str, float]
    decision: str
