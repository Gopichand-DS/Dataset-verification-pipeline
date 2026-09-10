from pathlib import Path
import json
import subprocess
import sys

def test_quality_report_understands_workflow_json(tmp_path):
    p = tmp_path / "workflow.json"
    p.write_text(json.dumps({
        "metrics": {"discovered": 5, "verified": 3, "rejected": 2},
        "source_health": [{"status": "ok"}, {"status": "blocked_or_rate_limited"}],
        "records": [
            {"name": "A", "official_url": "https://a.example",
             "verification_status": "verified",
             "verification_evidence": {"status": "verified"},
             "acceptance": {"accepted": True}},
            {"name": "B", "official_url": "https://b.example",
             "verification_status": "verified",
             "verification_evidence": {"status": "verified"},
             "acceptance": {"accepted": True}},
            {"name": "C", "official_url": "https://c.example",
             "verification_status": "verified",
             "verification_evidence": {"status": "verified"},
             "acceptance": {"accepted": True}},
        ]
    }), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "scripts/data_quality_report.py", str(p)],
        capture_output=True, text=True, check=True
    )
    data = json.loads(result.stdout)
    assert data["rows"] == 3
    assert data["independently_verified"] == 3
    assert data["acceptance_passed"] == 3
    assert data["source_health"]["blocked_or_rate_limited"] == 1
