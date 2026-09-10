
from app.adapters.webpage import WebPageAdapter


class FakeResponse:
    status_code = 200
    url = "https://example.com/"
    text = """
    <html>
      <head>
        <title>Example AI Tool</title>
        <meta name="description" content="An AI tool">
        <link rel="canonical" href="https://example.com/">
      </head>
      <body><h1>Example AI Tool</h1><p>API available.</p></body>
    </html>
    """


def test_webpage_adapter(monkeypatch):
    adapter = WebPageAdapter()

    def fake_fetch(url):
        return FakeResponse()

    monkeypatch.setattr(adapter, "fetch", fake_fetch)
    item = adapter.discover("https://example.com/")[0]

    assert item["title"] == "Example AI Tool"
    assert item["canonical_url"] == "https://example.com/"
    assert item["status_code"] == 200
