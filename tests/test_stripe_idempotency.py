import sqlite3

from app.config import settings
from app.storage import (
    claim_stripe_event,
    complete_stripe_event,
    fail_stripe_event,
    init_db,
)


def test_stripe_webhook_event_is_idempotent_and_failed_event_can_retry(tmp_path, monkeypatch):
    database = tmp_path / "stripe-events.sqlite3"
    monkeypatch.setattr(settings, "database_path", str(database))
    init_db()

    assert claim_stripe_event("evt_123", "checkout.session.completed") is True
    assert claim_stripe_event("evt_123", "checkout.session.completed") is False

    fail_stripe_event("evt_123")
    assert claim_stripe_event("evt_123", "checkout.session.completed") is True

    complete_stripe_event("evt_123")
    assert claim_stripe_event("evt_123", "checkout.session.completed") is False


def test_stale_processing_stripe_event_can_be_reclaimed(tmp_path, monkeypatch):
    database = tmp_path / "stripe-events-stale.sqlite3"
    monkeypatch.setattr(settings, "database_path", str(database))
    init_db()

    assert claim_stripe_event("evt_stale", "checkout.session.completed") is True
    with sqlite3.connect(database) as conn:
        conn.execute(
            "UPDATE stripe_webhook_events SET updated_at=datetime('now', '-11 minutes') WHERE event_id=?",
            ("evt_stale",),
        )

    assert claim_stripe_event("evt_stale", "checkout.session.completed") is True
    assert claim_stripe_event("evt_stale", "checkout.session.completed") is False
