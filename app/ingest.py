import pandas as pd
import json
from app.db import SessionLocal, Record
from app.normalize import canonical_key, normalize_url, json_safe

def ingest_file(module, path):
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    elif suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        df = pd.DataFrame(data if isinstance(data, list) else data.get("records", []))
    else:
        raise ValueError("Supported input formats: CSV, XLSX, JSON")

    db = SessionLocal()
    count = 0
    for row in df.fillna("").to_dict("records"):
        name = row.get("name") or row.get("tool_name") or row.get("company_name") or row.get("model_name")
        if not name:
            continue
        url = row.get("official_url") or row.get("website") or row.get("url")
        company = row.get("company") or row.get("manufacturer") or row.get("provider") or ""
        key = canonical_key(name, url, company)
        existing = db.query(Record).filter_by(canonical_key=key, module=module).first()
        if existing:
            continue
        db.add(Record(
            module=module,
            canonical_key=key,
            name=name,
            official_url=normalize_url(url) if url else None,
            company=company,
            raw_json=json_safe(row),
            status="raw"
        ))
        count += 1
    db.commit()
    db.close()
    return count
