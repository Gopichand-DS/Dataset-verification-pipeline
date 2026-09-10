def test_discovery_imports():
    from app.discovery.engine import DiscoveryEngine
    from app.discovery.health import classify_http
    assert DiscoveryEngine is not None
    assert classify_http(200) == "ok"
