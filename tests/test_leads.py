from fastapi.testclient import TestClient
from app.main import app
from app import research

client = TestClient(app)


def test_lead_finder_rejects_unsupported_language():
    response = client.post("/api/v1/leads/find", json={
        "industry": "Software",
        "target_market": "Spain",
        "ideal_customer": "Mid-sized logistics companies",
        "language": "xx",
    })
    assert response.status_code == 400


def test_company_search_returns_empty_without_tavily_key(monkeypatch):
    monkeypatch.setattr(research.settings, "tavily_api_key", "")
    assert research.search_business_leads(
        "Software", "Spain", "Mid-sized logistics companies"
    ) == []


def test_lead_finder_validates_request_and_caps_results():
    response = client.post("/api/v1/leads/find", json={
        "industry": "Software",
        "target_market": "Spain",
        "ideal_customer": "Mid-sized logistics companies",
        "max_results": 21,
    })
    assert response.status_code == 422
