from app.discovery.workflow import DiscoveryWorkflow


def test_common_dataset_identity_aliases_enter_verification():
    wf = DiscoveryWorkflow()
    rows = wf._prepare([
        {"toolName": "Example Tool", "websiteUrl": "https://example.com", "description": "An AI tool"}
    ], "tools", "test.csv")
    assert len(rows) == 1
    row = rows[0]
    assert row.get("record_status") != "left_unprocessed"
    assert row["name"] == "Example Tool"
    assert row["official_url"] == "https://example.com"
    assert row["_input_fields"]
