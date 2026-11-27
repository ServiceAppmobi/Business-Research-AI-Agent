import json
from fastapi.testclient import TestClient
from app.main import app
from app import main

client = TestClient(app)

def test_pdf_endpoint_returns_404_for_unknown_order(monkeypatch):
    monkeypatch.setattr(main, "get_order", lambda order_id: None)
    response = client.get("/api/v1/orders/missing/report.pdf")
    assert response.status_code == 404

def test_pdf_endpoint_returns_pdf_for_completed_order(monkeypatch):
    report = {
        "executive_summary": "Market entry opportunity",
        "market_overview": "Growing market",
        "target_customers": ["Small businesses"],
        "opportunities": ["Digital services"],
        "risks": ["Competition"],
        "competitor_landscape": ["Competitor A"],
        "recommended_next_steps": ["Interview customers"],
        "assumptions_and_limitations": ["Limited public evidence"],
        "citations": [{"title": "Example source", "url": "https://example.com", "snippet": "Evidence"}],
        "research_method": "Test fixture",
        "disclaimer": "For information only",
    }
    monkeypatch.setattr(main, "get_order", lambda order_id: {
        "status": "completed",
        "report_json": json.dumps(report),
    })
    response = client.get("/api/v1/orders/test-order/report.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
