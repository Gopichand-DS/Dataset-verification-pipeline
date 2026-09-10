from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.modules.schemas import ensure_module_schema, module_columns


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _key(record: dict[str, Any]) -> str:
    return str(
        record.get("canonical_key")
        or record.get("official_url")
        or record.get("website")
        or record.get("url")
        or record.get("ingest_row_key")
        or f"name:{str(record.get('name', '')).strip().lower()}"
    ).strip().lower()


def _merge_value(old: Any, new: Any) -> Any:
    if new is None or new == "" or new == [] or new == {}:
        return old
    return new


def _merge_record(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    merged = dict(old)
    for key, value in new.items():
        if key in {"discovery_sources", "source_urls", "sources"}:
            old_items = old.get(key) or []
            new_items = value or []
            if isinstance(old_items, list) and isinstance(new_items, list):
                merged[key] = list(dict.fromkeys([*old_items, *new_items]))
            else:
                merged[key] = _merge_value(old_items, new_items)
        else:
            merged[key] = _merge_value(old.get(key), value)
    merged["first_seen_at"] = old.get("first_seen_at") or _now()
    merged["last_seen_at"] = _now()
    merged["run_count"] = int(old.get("run_count") or 0) + 1
    return merged


def upsert_workflow_file(path: str | Path, workflow: dict[str, Any], *, fresh: bool = False) -> dict[str, Any]:
    """Update one persistent master file without dropping columns or records."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    module = workflow.get("module", "")

    existing_payload: dict[str, Any] = {}
    if target.exists() and not fresh:
        try:
            existing_payload = json.loads(target.read_text(encoding="utf-8"))
            if not isinstance(existing_payload, dict):
                existing_payload = {}
        except (OSError, json.JSONDecodeError):
            existing_payload = {}

    records: list[dict[str, Any]] = []
    index: dict[str, int] = {}
    existing_records = existing_payload.get("records", [])
    if isinstance(existing_records, list):
        for item in existing_records:
            if not isinstance(item, dict):
                continue
            item = ensure_module_schema(item, module)
            k = _key(item)
            if k in index:
                records[index[k]] = _merge_record(records[index[k]], item)
            else:
                item = dict(item)
                item.setdefault("first_seen_at", _now())
                item.setdefault("last_seen_at", item["first_seen_at"])
                item.setdefault("run_count", 1)
                index[k] = len(records)
                records.append(item)

    inserted = updated = 0
    incoming = workflow.get("records", []) or []
    # Backward compatible: older workflow payloads may only contain accepted records.
    for raw_item in incoming:
        if not isinstance(raw_item, dict):
            continue
        item = ensure_module_schema(raw_item, module)
        k = _key(item)
        if k in index:
            records[index[k]] = _merge_record(records[index[k]], item)
            updated += 1
        else:
            item = dict(item)
            item["first_seen_at"] = _now()
            item["last_seen_at"] = item["first_seen_at"]
            item["run_count"] = 1
            index[k] = len(records)
            records.append(item)
            inserted += 1

    # One stable column contract for the whole master file. Existing records get
    # blanks for fields discovered later; incoming/source columns are retained.
    columns = module_columns(module, records)
    for row in records:
        for column in columns:
            row.setdefault(column, "")

    payload = dict(workflow)
    payload["records"] = records
    payload["record_count"] = len(records)
    payload["accepted_record_count"] = sum(r.get("record_status") == "accepted" or (isinstance(r.get("acceptance"), dict) and r["acceptance"].get("accepted") is True) for r in records)
    payload["rejected_record_count"] = len(records) - payload["accepted_record_count"]
    payload["columns"] = columns
    payload["store"] = {
        "mode": "fresh" if fresh else "upsert",
        "file": str(target),
        "inserted": inserted,
        "updated": updated,
        "total": len(records),
        "columns": len(columns),
        "updated_at": _now(),
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload
