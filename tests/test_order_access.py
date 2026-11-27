from fastapi.testclient import TestClient

from app.main import app
from app import main
from app.config import settings
from app.storage import create_order, hash_access_token, init_db, verify_order_access

client = TestClient(app)


def test_order_access_token_is_hashed_and_verified(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "orders.sqlite3"))
    init_db()

    token = "long-random-order-token"
    create_order("order-1", "buyer@example.com", {"company": "Example"}, hash_access_token(token))

    assert verify_order_access("order-1", token) is True
    assert verify_order_access("order-1", "wrong-token") is False
    assert verify_order_access("missing-order", token) is False


def test_existing_database_gets_access_token_column(tmp_path, monkeypatch):
    import sqlite3

    database = tmp_path / "legacy.sqlite3"
    monkeypatch.setattr(settings, "database_path", str(database))
    with sqlite3.connect(database) as conn:
        conn.execute("""
            CREATE TABLE research_orders (
                id TEXT PRIMARY KEY,
                customer_email TEXT NOT NULL,
                request_json TEXT NOT NULL,
                stripe_session_id TEXT UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending_payment',
                report_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

    init_db()
    with sqlite3.connect(database) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(research_orders)")}
    assert "access_token_hash" in columns


def test_order_status_requires_valid_bearer_token(monkeypatch):
    monkeypatch.setattr(main, "verify_order_access", lambda order_id, token: token == "valid-token")
    monkeypatch.setattr(main, "get_order", lambda order_id: {
        "status": "paid",
        "created_at": "2026-11-27 12:00:00",
        "report_json": None,
    })

    assert client.get("/api/v1/orders/order-1").status_code == 401
    assert client.get(
        "/api/v1/orders/order-1",
        headers={"Authorization": "Bearer invalid-token"},
    ).status_code == 401

    response = client.get(
        "/api/v1/orders/order-1",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "paid"


def test_pdf_download_requires_valid_bearer_token(monkeypatch):
    monkeypatch.setattr(main, "verify_order_access", lambda order_id, token: token == "valid-token")
    monkeypatch.setattr(main, "get_order", lambda order_id: {
        "status": "completed",
        "report_json": '{"executive_summary":"Example"}',
    })

    assert client.get("/api/v1/orders/order-1/report.pdf").status_code == 401
    response = client.get(
        "/api/v1/orders/order-1/report.pdf",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
