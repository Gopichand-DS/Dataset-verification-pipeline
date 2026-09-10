
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from .db import SessionLocal, init_db
from .models import AuditLog, Record, VerificationEvent
from .dedupe import likely_duplicate
from .evidence import evidence_for_field
from .extraction import extract_public_fields
from .normalize import canonical_key, normalize_url
from .scoring_evidence import score_with_evidence
from .modules.registry import evaluate as evaluate_module
from .adapters.webpage import WebPageAdapter


def _dump(value):
    return json.dumps(value or {}, ensure_ascii=False, default=str)


def _load(value):
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value or "{}")
    except Exception:
        return {}


def _read_records(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    elif suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload if isinstance(payload, list) else payload.get("records", [])
        df = pd.DataFrame(rows)
    else:
        raise ValueError("Supported input formats: CSV, XLSX, JSON")
    return df.fillna("").to_dict("records")


class Pipeline:
    """
    End-to-end curation API:

    discovery/input -> raw storage -> independent official-source verification
    -> conservative enrichment -> dedupe -> evidence-backed scoring -> export.
    """

    def __init__(self, adapter=None):
        self.adapter = adapter or WebPageAdapter()

    def init_db(self):
        init_db()

    def ingest(self, module: str, input_file: Path):
        rows = _read_records(Path(input_file))
        init_db()
        count = 0
        with SessionLocal() as session:
            for row in rows:
                name = row.get("name") or row.get("tool_name") or row.get("company_name") or row.get("model_name") or row.get("title")
                if not name:
                    continue
                url = row.get("official_url") or row.get("website") or row.get("url") or ""
                company = row.get("company") or row.get("manufacturer") or row.get("provider") or ""
                key = canonical_key(name, url, company)
                existing = session.scalar(
                    select(Record).where(
                        Record.module == module,
                        Record.canonical_key == key,
                    )
                )
                if existing:
                    continue
                session.add(Record(
                    module=module,
                    canonical_key=key,
                    name=str(name),
                    official_url=normalize_url(url) if url else None,
                    company=str(company) if company else None,
                    raw_json=_dump(row),
                    normalized_json=_dump({}),
                    verification_json=_dump({}),
                    enrichment_json=_dump({}),
                    score_json=_dump({}),
                    status="raw",
                ))
                count += 1
            session.commit()
        return count

    def verify(self, module: str):
        init_db()
        with SessionLocal() as session:
            ids = [r.id for r in session.scalars(
                select(Record).where(Record.module == module, Record.status == "raw")
            )]
        results = []
        for record_id in ids:
            results.append(verify_record(record_id, adapter=self.adapter))
        return results

    def curate(self, module: str):
        return curate_records(module)

    def export(self, module: str, output_file: Path):
        init_db()
        rows = []
        with SessionLocal() as session:
            records = list(session.scalars(
                select(Record).where(
                    Record.module == module,
                    Record.status == "curated",
                )
            ))
            for r in records:
                row = _load(r.normalized_json) or _load(r.raw_json)
                row.update({
                    "record_id": r.id,
                    "module": r.module,
                    "canonical_key": r.canonical_key,
                    "name": r.name,
                    "official_url": r.official_url,
                    "company": r.company,
                    "status": r.status,
                    "verification": _load(r.verification_json),
                    "enrichment": _load(r.enrichment_json),
                    "score": _load(r.score_json),
                })
                rows.append(row)

        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if output_file.suffix.lower() == ".json":
            output_file.write_text(json.dumps(rows, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        elif output_file.suffix.lower() == ".csv":
            pd.DataFrame(rows).to_csv(output_file, index=False)
        else:
            raise ValueError("Output format must be JSON or CSV")
        return len(rows)


def ingest_candidates(candidates, module):
    init_db()
    ids = []
    with SessionLocal() as session:
        for c in candidates:
            raw = dict(c)
            name = raw.get("name") or raw.get("title") or "Unnamed candidate"
            url = raw.get("official_url") or raw.get("website") or raw.get("url")
            company = raw.get("company")
            record = Record(
                module=module,
                canonical_key=canonical_key(name, url, company),
                name=name,
                official_url=normalize_url(url) if url else None,
                company=company,
                raw_json=_dump(raw),
                normalized_json=_dump({}),
                verification_json=_dump({}),
                enrichment_json=_dump({}),
                score_json=_dump({}),
                status="raw",
            )
            session.add(record)
            session.flush()
            ids.append(record.id)
        session.commit()
    return ids


def verify_record(record_id, adapter=None):
    adapter = adapter or WebPageAdapter()
    init_db()
    with SessionLocal() as session:
        record = session.scalar(select(Record).where(Record.id == record_id))
        if not record:
            raise ValueError(f"Record {record_id} not found")

        raw = _load(record.raw_json)
        official = raw.get("official_url") or raw.get("website") or raw.get("url") or record.official_url

        if not official:
            record.status = "review"
            record.verification_json = _dump({
                "verified": False,
                "reason": "missing_official_url",
                "verified_at": datetime.now(timezone.utc).isoformat(),
            })
            session.add(AuditLog(record_id=record.id, action="verify", details="Missing official URL"))
            session.commit()
            return _load(record.verification_json)

        try:
            page = adapter.discover(official)[0]
        except Exception as exc:
            record.status = "review"
            record.verification_json = _dump({
                "verified": False,
                "reason": "fetch_failed",
                "error": str(exc),
                "source_url": official,
                "verified_at": datetime.now(timezone.utc).isoformat(),
            })
            session.add(AuditLog(record_id=record.id, action="verify", details=f"Fetch failed: {exc}"))
            session.commit()
            return _load(record.verification_json)

        evidence = []
        for field in ("name", "description", "website", "official_url"):
            value = raw.get(field) or (record.name if field == "name" else None) or (record.official_url if field == "official_url" else None)
            if not value:
                continue
            ev = evidence_for_field(
                field=field,
                value=value,
                source_url=page["final_url"],
                page_title=page.get("title", ""),
                page_description=page.get("description", ""),
                page_text=page.get("text", ""),
            )
            evidence.append(ev.to_dict())
            session.add(VerificationEvent(
                record_id=record.id,
                field_name=field,
                ingested_value=str(value),
                verified_value=str(value) if ev.confidence > 0 else None,
                result="verified" if ev.confidence > 0 else "unsupported",
                source_url=ev.source_url,
                evidence=ev.evidence_text,
            ))

        verified = bool(page.get("status_code", 0) < 400 and any(
            e["field"] in {"name", "official_url", "website"} and e["confidence"] > 0
            for e in evidence
        ))

        verification = {
            "verified": verified,
            "source_url": page["final_url"],
            "canonical_url": page.get("canonical_url"),
            "status_code": page["status_code"],
            "page_title": page.get("title", ""),
            "evidence": evidence,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

        enrichment = extract_public_fields(page)
        record.verification_json = _dump(verification)
        record.enrichment_json = _dump(enrichment)
        record.normalized_json = _dump({**raw, **enrichment})
        record.status = "verified" if verified else "review"
        session.add(AuditLog(
            record_id=record.id,
            action="verify",
            details=_dump(verification)[:4000],
        ))
        session.commit()
        return verification


def curate_records(module):
    init_db()
    output = []
    with SessionLocal() as session:
        records = list(session.scalars(
            select(Record).where(Record.module == module)
        ))
        kept = []

        for record in records:
            data = _load(record.normalized_json) or _load(record.raw_json)

            duplicate_of = None
            for existing in kept:
                if likely_duplicate(
                    {"name": record.name, "official_url": record.official_url, "company": record.company},
                    {"name": existing.name, "official_url": existing.official_url, "company": existing.company},
                ):
                    duplicate_of = existing
                    break

            if duplicate_of:
                record.status = "duplicate"
                record.score_json = _dump({
                    "decision": "duplicate",
                    "duplicate_of": duplicate_of.id,
                })
                continue

            kept.append(record)

            if record.status not in {"verified", "review"}:
                continue

            evidence = _load(record.verification_json).get("evidence", [])
            factors = evaluate_module(module, data, evidence)
            score = score_with_evidence(factors, evidence)
            record.score_json = _dump(score)
            record.status = {
                "curate": "curated",
                "review": "review",
                "reject": "rejected",
            }[score["decision"]]
            output.append({
                "id": record.id,
                "status": record.status,
                "score": score["overall"],
            })

        session.commit()
    return output
