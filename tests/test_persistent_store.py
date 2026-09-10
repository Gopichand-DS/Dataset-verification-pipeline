import json
from pathlib import Path

from app.discovery.persistent_store import upsert_workflow_file


def test_workflow_file_upserts_without_duplicates(tmp_path: Path):
    path = tmp_path / "tools_master.json"
    first = {
        "module": "tools",
        "metrics": {"discovered": 1},
        "source_health": [],
        "records": [{
            "name": "Alpha",
            "canonical_key": "alpha|https://alpha.example",
            "official_url": "https://alpha.example",
            "description": "old",
            "discovery_sources": ["source-a"],
        }],
    }
    out1 = upsert_workflow_file(path, first)
    assert out1["store"]["inserted"] == 1
    assert out1["store"]["total"] == 1

    second = {
        "module": "tools",
        "metrics": {"discovered": 2},
        "source_health": [],
        "records": [
            {
                "name": "Alpha",
                "canonical_key": "alpha|https://alpha.example",
                "official_url": "https://alpha.example",
                "description": "new verified description",
                "discovery_sources": ["source-b"],
            },
            {
                "name": "Beta",
                "canonical_key": "beta|https://beta.example",
                "official_url": "https://beta.example",
            },
        ],
    }
    out2 = upsert_workflow_file(path, second)
    assert out2["store"]["inserted"] == 1
    assert out2["store"]["updated"] == 1
    assert out2["store"]["total"] == 2

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(payload["records"]) == 2
    alpha = next(r for r in payload["records"] if r["name"] == "Alpha")
    assert alpha["description"] == "new verified description"
    assert alpha["discovery_sources"] == ["source-a", "source-b"]
    assert alpha["run_count"] == 2


def test_blank_new_value_does_not_erase_existing(tmp_path: Path):
    path = tmp_path / "tools_master.json"
    upsert_workflow_file(path, {
        "module": "tools", "records": [{"name": "Alpha", "official_url": "https://alpha.example", "description": "kept"}]
    })
    out = upsert_workflow_file(path, {
        "module": "tools", "records": [{"name": "Alpha", "official_url": "https://alpha.example", "description": ""}]
    })
    assert out["records"][0]["description"] == "kept"
