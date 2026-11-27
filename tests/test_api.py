from fastapi.testclient import TestClient
from app.config import settings
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_languages_endpoint_has_eleven_languages():
    response = client.get("/api/v1/languages")
    assert response.status_code == 200
    assert len(response.json()) == 11

def test_research_rejects_unsupported_language(monkeypatch):
    monkeypatch.setattr(settings, "allow_direct_ai_api", True)
    response = client.post("/api/v1/research", json={
        "company": "Example Ltd",
        "industry": "Software",
        "target_market": "Spain",
        "research_goal": "Assess market entry",
        "language": "xx"
    })
    assert response.status_code == 400


def test_pricing_endpoint_returns_three_pln_tiers():
    response = client.get("/api/v1/pricing")
    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "PLN"
    assert {p["id"]: p["price"] for p in data["plans"]} == {
        "basic": 49.0,
        "professional": 99.0,
        "premium": 199.0,
    }


def test_checkout_rejects_unknown_report_tier():
    response = client.post("/api/v1/checkout", json={
        "customer_email": "buyer@example.com",
        "plan": "gold",
        "research": {
            "company": "Example Ltd",
            "industry": "Software",
            "target_market": "Poland",
            "research_goal": "Assess market entry",
            "language": "en"
        }
    })
    assert response.status_code == 422

    
def test_direct_ai_endpoints_are_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "allow_direct_ai_api", False)
    research = client.post("/api/v1/research", json={
        "company": "Example Ltd",
        "industry": "Software",
        "target_market": "Spain",
        "research_goal": "Assess market entry",
        "language": "en"
    })
    leads = client.post("/api/v1/leads/find", json={
        "industry": "Software",
        "target_market": "Spain",
        "ideal_customer": "Mid-sized companies"
    })
    assert research.status_code == 403
    assert leads.status_code == 403


def test_checkout_requires_transactional_email_configuration(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "")
    monkeypatch.setattr(settings, "email_from", "")
    response = client.post("/api/v1/checkout", json={
        "customer_email": "buyer@example.com",
        "plan": "professional",
        "research": {
            "company": "Example Ltd",
            "industry": "Software",
            "target_market": "Poland",
            "research_goal": "Assess market entry",
            "language": "en"
        }
    })
    assert response.status_code == 503
    assert "email is not configured" in response.json()["detail"].lower()

