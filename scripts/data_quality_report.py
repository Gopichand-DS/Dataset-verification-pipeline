from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def load_payload(path: Path):
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        return {"records": rows, "source_health": []}

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {"records": data, "source_health": []}
        return {
            "records": data.get("records", data.get("candidates", [])),
            "source_health": data.get("source_health", data.get("sources", [])),
            "metrics": data.get("metrics", {}),
        }

    with path.open(newline="", encoding="utf-8-sig") as f:
        return {"records": list(csv.DictReader(f)), "source_health": []}


def main():
    p = argparse.ArgumentParser(description="Report AIOrbit data quality and verification coverage.")
    p.add_argument("file")
    args = p.parse_args()

    payload = load_payload(Path(args.file))
    rows = payload["records"]
    sources = payload.get("source_health", [])
    total = len(rows)

    missing_name = sum(not str(r.get("name", "")).strip() for r in rows)
    missing_url = sum(not str(r.get("official_url", "")).strip() for r in rows)

    verified = sum(
        r.get("verification_status") in {"verified", "partially_verified"}
        for r in rows
    )
    accepted = sum(
        isinstance(r.get("acceptance"), dict) and r["acceptance"].get("accepted") is True
        for r in rows
    )
    evidence = sum(bool(r.get("verification_evidence")) for r in rows)

    # A reachability verification is not equivalent to field-level verification.
    field_evidence = sum(
        bool(r.get("field_evidence") or r.get("verification_events") or r.get("evidence"))
        for r in rows
    )

    source_counts = Counter(str(x.get("status", "unknown")) for x in sources)
    record_status = Counter(
        str(
            r.get("status")
            or r.get("lifecycle_status")
            or r.get("acceptance", {}).get("accepted") if isinstance(r.get("acceptance"), dict) else r.get("status")
            or "unknown"
        )
        for r in rows
    )

    report = {
        "rows": total,
        "missing_name": missing_name,
        "missing_official_url": missing_url,
        "independently_verified": verified,
        "not_independently_verified": total - verified,
        "acceptance_passed": accepted,
        "rejected_records": total - accepted,
        "verification_evidence_present": evidence,
        "field_level_evidence_present": field_evidence,
        "source_health": dict(source_counts),
        "record_status_distribution": dict(record_status),
        "quality_flags": {
            "verification_rate": round(verified / total, 4) if total else 0,
            "acceptance_rate": round(accepted / total, 4) if total else 0,
            "rejection_rate": round((total - accepted) / total, 4) if total else 0,
            "evidence_coverage": round(evidence / total, 4) if total else 0,
            "field_evidence_coverage": round(field_evidence / total, 4) if total else 0,
            "name_completeness": round((total - missing_name) / total, 4) if total else 0,
            "official_url_completeness": round((total - missing_url) / total, 4) if total else 0,
        },
        "interpretation": (
            "verification_status='verified' currently means the official URL passed "
            "the reachability/content gate. It does not prove every product field. "
            "Field-level evidence coverage is reported separately."
        ),
        "pipeline_metrics": payload.get("metrics", {}),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
