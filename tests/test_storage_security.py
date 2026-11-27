from app import storage
from app.config import settings


def test_order_access_token_is_stored_as_hash_and_verified(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "orders.sqlite3"))
    storage.init_db()
    token = "test-access-token"
    storage.create_order(
        "order-1",
        "buyer@example.com",
        {"company": "Example Ltd"},
        storage.hash_access_token(token),
    )
    order = storage.get_order("order-1")
    assert order["access_token_hash"] != token
    assert storage.verify_order_access("order-1", token)
    assert not storage.verify_order_access("order-1", "wrong-token")
    assert not storage.verify_order_access("missing-order", token)


def test_failed_stripe_event_can_be_reclaimed_but_completed_event_cannot(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "orders.sqlite3"))
    storage.init_db()
    assert storage.claim_stripe_event("evt-failed", "checkout.session.completed")
    storage.fail_stripe_event("evt-failed")
    assert storage.claim_stripe_event("evt-failed", "checkout.session.completed")
    storage.complete_stripe_event("evt-failed")
    assert not storage.claim_stripe_event("evt-failed", "checkout.session.completed")
