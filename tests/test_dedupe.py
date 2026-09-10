from app.dedupe import likely_duplicate

def test_same_url_duplicate():
    a = {"name": "Tool A", "official_url": "https://example.com", "company": "Acme"}
    b = {"name": "Tool A Listing", "official_url": "https://example.com/", "company": "Acme"}
    assert likely_duplicate(a, b)
