from app.discovery.tool_enrichment import canonical_tool_id
from app.discovery.workflow import DiscoveryWorkflow


def test_canonical_tool_id_stable():
    assert canonical_tool_id("Example AI", "https://example.com/") == canonical_tool_id("Example AI", "https://example.com/")


def test_missing_identity_row_left_unprocessed():
    wf = DiscoveryWorkflow()
    rows = wf._prepare([{"name": "", "websiteUrl": "", "description": "anything"}], "tools", "input.csv")
    assert len(rows) == 1
    assert rows[0]["record_status"] == "left_unprocessed"
    assert rows[0]["verification_status"] == "not_checked_missing_identity"


def test_missing_identity_row_is_retained():
    wf = DiscoveryWorkflow()
    rows = wf._prepare([
        {"name": "", "websiteUrl": "", "description": "anything"},
        {"name": "Good", "websiteUrl": "https://example.com"},
    ], "tools", "input.csv")
    assert any(r.get("record_status") == "left_unprocessed" for r in rows)
