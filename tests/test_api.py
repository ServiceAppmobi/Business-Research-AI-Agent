from fastapi.testclient import TestClient
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

def test_research_rejects_unsupported_language():
    response = client.post("/api/v1/research", json={
        "company": "Example Ltd",
        "industry": "Software",
        "target_market": "Spain",
        "research_goal": "Assess market entry",
        "language": "xx"
    })
    assert response.status_code == 400
