from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_customer_portal_is_served():
    response = client.get("/portal")
    assert response.status_code == 200
    assert "Secure customer portal" in response.text
    assert "Open my report" in response.text
    assert "localStorage" not in response.text


def test_portal_does_not_expose_order_data_in_page():
    response = client.get("/portal")
    assert response.status_code == 200
    assert "access_token" not in response.text
    assert "customer_email" not in response.text
