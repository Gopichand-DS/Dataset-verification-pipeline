from app.discovery.acceptance import acceptance_report
from app.discovery.health import classify_http

def test_blocked_http_is_not_success():
    assert classify_http(403) == "blocked_or_rate_limited"
    assert classify_http(429) == "blocked_or_rate_limited"

def test_unverified_candidate_cannot_be_accepted():
    report = acceptance_report("tools", {
        "name":"Example",
        "official_url":"https://example.com",
        "verification_status":"unverified",
        "discovery_sources":["Directory"],
    })
    assert report["accepted"] is False
    assert "not_independently_verified" in report["reasons"]

def test_verified_candidate_can_pass_basic_gate():
    report = acceptance_report("tools", {
        "name":"Example",
        "official_url":"https://example.com",
        "verification_status":"verified",
        "discovery_sources":["Directory"],
    })
    assert report["accepted"] is True
