from __future__ import annotations
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CHECKS = [
    "app.models",
    "app.pipeline",
    "app.discovery.engine",
    "app.discovery.verification_gate",
    "app.discovery.acceptance",
]


def main():
    failures = []
    for name in CHECKS:
        try:
            importlib.import_module(name)
            print(f"OK   {name}")
        except Exception as exc:
            failures.append((name, str(exc)))
            print(f"FAIL {name}: {exc}")
    if failures:
        raise SystemExit(1)
    print("AIOrbit healthcheck: PASS")


if __name__ == "__main__":
    main()
