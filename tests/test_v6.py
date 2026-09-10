from app.discovery.health import classify_http
from app.discovery.verification_cache import VerificationCache
from app.monitoring.metrics import summarize_source_health

def test_health_classification():
    assert classify_http(200) == "ok"
    assert classify_http(403) == "blocked_or_rate_limited"
    assert classify_http(429) == "blocked_or_rate_limited"

def test_source_health_summary():
    assert summarize_source_health([
        {"status":"ok"}, {"status":"ok"}, {"status":"error"},
        {"status":"blocked_or_rate_limited"}
    ]) == {"ok":2,"error":1,"blocked_or_rate_limited":1}

def test_cache_roundtrip(tmp_path):
    c = VerificationCache(tmp_path/"cache.json")
    c.put("https://example.com", {"status":"verified"})
    assert c.get("https://example.com")["status"] == "verified"
