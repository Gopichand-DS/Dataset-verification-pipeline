from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class Record(Base):
    __tablename__ = "records"
    id = Column(Integer, primary_key=True)
    module = Column(String(40), index=True, nullable=False)
    canonical_key = Column(String(512), index=True, nullable=False)
    name = Column(String(512), index=True, nullable=False)
    official_url = Column(Text)
    company = Column(String(512))
    raw_json = Column(Text, nullable=False)
    normalized_json = Column(Text)
    verification_json = Column(Text)
    enrichment_json = Column(Text)
    score_json = Column(Text)
    status = Column(String(40), default="raw", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class VerificationEvent(Base):
    __tablename__ = "verification_events"
    id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey("records.id"), index=True)
    field_name = Column(String(256), index=True)
    ingested_value = Column(Text)
    verified_value = Column(Text)
    result = Column(String(40))
    source_url = Column(Text)
    evidence = Column(Text)
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey("records.id"), index=True)
    action = Column(String(80))
    details = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
