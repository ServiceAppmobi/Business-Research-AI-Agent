from app import research

class FakeResponse:
    def raise_for_status(self):
        return None
    def json(self):
        return {"results": [
            {"title": "Market report", "url": "https://example.com/report", "content": "Relevant market evidence", "score": 0.9},
            {"title": "Market report duplicate", "url": "https://example.com/report", "content": "Duplicate", "score": 0.8},
        ]}

def test_search_returns_empty_without_api_key(monkeypatch):
    monkeypatch.setattr(research.settings, "tavily_api_key", "")
    assert research.search_web("Acme", "Software", "Spain", "Market entry") == []

def test_search_deduplicates_urls_and_uses_bearer_auth(monkeypatch):
    monkeypatch.setattr(research.settings, "tavily_api_key", "test-key")
    calls = []
    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()
    monkeypatch.setattr(research.requests, "post", fake_post)
    results = research.search_web("Acme", "Software", "Spain", "Market entry")
    assert len(results) == 1
    assert results[0]["url"] == "https://example.com/report"
    assert calls[0][1]["headers"]["Authorization"] == "Bearer test-key"
    assert len(calls) == 4
