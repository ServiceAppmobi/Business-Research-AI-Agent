import hashlib
import hmac
import json
import sqlite3
from pathlib import Path
from typing import Any
from app.config import settings

def _connect():
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def hash_access_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def init_db():
    with _connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS research_orders (
            id TEXT PRIMARY KEY,
            customer_email TEXT NOT NULL,
            request_json TEXT NOT NULL,
            stripe_session_id TEXT UNIQUE,
            status TEXT NOT NULL DEFAULT 'pending_payment',
            report_json TEXT,
            access_token_hash TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(research_orders)")}
        if "access_token_hash" not in columns:
            conn.execute("ALTER TABLE research_orders ADD COLUMN access_token_hash TEXT")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS stripe_webhook_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'processing',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

def create_order(order_id: str, email: str, request_data: dict[str, Any], access_token_hash: str):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO research_orders (id, customer_email, request_json, access_token_hash) VALUES (?, ?, ?, ?)",
            (order_id, email, json.dumps(request_data, ensure_ascii=False), access_token_hash),
        )

def verify_order_access(order_id: str, token: str) -> bool:
    if not token:
        return False
    with _connect() as conn:
        row = conn.execute(
            "SELECT access_token_hash FROM research_orders WHERE id=?",
            (order_id,),
        ).fetchone()
    stored_hash = row["access_token_hash"] if row else None
    return bool(stored_hash and hmac.compare_digest(stored_hash, hash_access_token(token)))

def attach_checkout(order_id: str, session_id: str):
    with _connect() as conn:
        conn.execute(
            "UPDATE research_orders SET stripe_session_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (session_id, order_id),
        )

def get_order(order_id: str):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM research_orders WHERE id=?", (order_id,)).fetchone()
    return dict(row) if row else None

def mark_paid(order_id: str):
    with _connect() as conn:
        conn.execute(
            """UPDATE research_orders SET status='paid', updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND status='pending_payment'""",
            (order_id,),
        )

def save_report(order_id: str, report: dict[str, Any]):
    with _connect() as conn:
        conn.execute(
            """UPDATE research_orders SET status='completed', report_json=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND status IN ('paid','generating')""",
            (json.dumps(report, ensure_ascii=False), order_id),
        )

def claim_generation(order_id: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            """UPDATE research_orders SET status='generating', updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND status='paid'""",
            (order_id,),
        )
        return cur.rowcount == 1

def mark_failed(order_id: str):
    with _connect() as conn:
        conn.execute(
            """UPDATE research_orders SET status='paid', updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND status='generating'""",
            (order_id,),
        )

def mark_payment_failed(order_id: str):
    with _connect() as conn:
        conn.execute(
            """UPDATE research_orders SET status='payment_failed', updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND status='pending_payment'""",
            (order_id,),
        )

def claim_stripe_event(event_id: str, event_type: str) -> bool:
    with _connect() as conn:
        inserted = conn.execute(
            """INSERT OR IGNORE INTO stripe_webhook_events (event_id, event_type, status)
               VALUES (?, ?, 'processing')""",
            (event_id, event_type),
        )
        if inserted.rowcount == 1:
            return True
        reclaimed = conn.execute(
            """UPDATE stripe_webhook_events
               SET status='processing', event_type=?, updated_at=CURRENT_TIMESTAMP
               WHERE event_id=? AND (
                   status='failed'
                   OR (status='processing' AND julianday('now') - julianday(updated_at) > (10.0 / 1440.0))
               )""",
            (event_type, event_id),
        )
        return reclaimed.rowcount == 1

def complete_stripe_event(event_id: str):
    with _connect() as conn:
        conn.execute(
            """UPDATE stripe_webhook_events SET status='completed', updated_at=CURRENT_TIMESTAMP
               WHERE event_id=?""",
            (event_id,),
        )

def fail_stripe_event(event_id: str):
    with _connect() as conn:
        conn.execute(
            """UPDATE stripe_webhook_events SET status='failed', updated_at=CURRENT_TIMESTAMP
               WHERE event_id=? AND status='processing'""",
            (event_id,),
        )
