from app.normalize import normalize_url, canonical_key

def test_normalize_url():
    assert normalize_url("http://www.Example.com/foo/?x=1") == "https://example.com/foo"

def test_canonical_key():
    assert canonical_key("Example", "https://example.com", "Acme") == "example.com|example|acme"
