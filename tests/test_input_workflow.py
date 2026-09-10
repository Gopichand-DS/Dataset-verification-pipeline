from app.discovery.workflow import DiscoveryWorkflow


class DummyCache:
    def get(self, url): return None
    def put(self, url, value): pass


def test_input_workflow_keeps_all_columns(monkeypatch):
    from app.discovery import workflow
    monkeypatch.setattr(workflow, "verify_official_url", lambda url: type("R", (), {
        "to_dict": lambda self: {"status": "verified", "checked_at": "now", "url": url}
    })())
    rows = [{
        "name": "News Bot", "official_url": "https://example.com",
        "description": "AI news chatbot", "original_a": "x", "original_b": "y"
    }]
    result = DiscoveryWorkflow(cache=DummyCache()).run("tools", input_records=rows)
    assert len(result["records"]) == 1
    record = result["records"][0]
    assert record["original_a"] == "x"
    assert record["original_b"] == "y"
    assert record["aiorbit_category"] == "Other/Unclassified"
    assert record["verification_status"] == "unverified"


def test_input_claims_are_never_trusted_and_fields_get_verdicts(monkeypatch):
    from app.discovery import workflow
    monkeypatch.setattr(workflow, "verify_official_url", lambda url: type("R", (), {
        "to_dict": lambda self: {
            "status": "verified", "checked_at": "now", "url": url,
            "final_url": url, "http_status": 200,
            "title": "Acme News AI", "description": "AI news assistant",
            "text": "Acme News AI is an AI news assistant for journalists. API available.",
            "links": [url + "/api"],
        }
    })())
    rows = [{
        "name": "Acme News AI", "websiteUrl": "https://example.com",
        "description": "AI news assistant", "pricingAmount": "$9999",
        "toolCategories": "Finance", "views": 12345,
    }]
    result = DiscoveryWorkflow(cache=DummyCache()).run("tools", input_records=rows)
    record = result["records"][0]
    fields = record["field_verification"]["fields"]
    assert fields["description"]["status"] == "verified"
    assert fields["pricingAmount"]["status"] == "unsupported"
    assert fields["views"]["status"] == "unverified_external_claim"
    assert record["aiorbit_category"] == "News"
    assert record["toolCategories"] == "Finance"


def test_valid_identity_with_unsupported_fields_is_not_rejected(monkeypatch):
    from app.discovery import workflow
    monkeypatch.setattr(workflow, "verify_official_url", lambda url: type("R", (), {
        "to_dict": lambda self: {
            "status": "verified", "checked_at": "now", "url": url,
            "final_url": url, "http_status": 200,
            "title": "Real Tool", "description": "Real Tool helps users automate work",
            "text": "Real Tool helps users automate work. Pricing is available on request.",
            "links": [],
        }
    })())
    rows = [{
        "name": "Real Tool", "websiteUrl": "https://example.com",
        "views": 12345, "avgRating": 4.9,
    }]
    result = DiscoveryWorkflow(cache=DummyCache()).run("tools", input_records=rows)
    record = result["records"][0]
    assert record["verification_status"] == "verified"
    assert record["record_status"] == "accepted"
    assert record["quality_filter"] == "green"
    assert result["metrics"]["ingested"] == 1
    assert result["metrics"]["verified"] == 1
    assert result["metrics"]["curated"] == 1
    assert result["metrics"]["rejected"] == 0


def test_contradicted_input_is_red(monkeypatch):
    from app.discovery import workflow
    monkeypatch.setattr(workflow, "verify_official_url", lambda url: type("R", (), {
        "to_dict": lambda self: {
            "status": "verified", "checked_at": "now", "url": url,
            "final_url": url, "http_status": 200,
            "title": "Real Tool", "description": "Real Tool is a coding assistant",
            "text": "Real Tool is a coding assistant for developers. This product does not provide an API.",
            "links": [],
        }
    })())
    rows = [{"name": "Real Tool", "websiteUrl": "https://example.com", "hasApi": True}]
    result = DiscoveryWorkflow(cache=DummyCache()).run("tools", input_records=rows)
    record = result["records"][0]
    assert record["record_status"] == "rejected"
    assert record["quality_filter"] == "red"
    assert "contradicted_input_fields" in record["acceptance"]["reasons"]
