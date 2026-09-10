
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from app.adapters.webpage import WebPageAdapter
from app.pipeline import ingest_candidates, curate_records, verify_record


def load_yaml(path: str):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Run a public-source AIOrbit curation pass.")
    parser.add_argument("--module", default="tools")
    parser.add_argument("--url", action="append", required=True, help="Public source page to fetch.")
    args = parser.parse_args()

    adapter = WebPageAdapter()
    candidates = []
    for url in args.url:
        candidates.extend(adapter.discover(url))

    ids = ingest_candidates(candidates, args.module)
    for record_id in ids:
        verify_record(record_id, adapter=adapter)

    results = curate_records(args.module)
    print(f"ingested={len(ids)} curated_pass={len(results)}")
    for item in results:
        print(item)


if __name__ == "__main__":
    main()
