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
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

def create_order(order_id: str, email: str, request_data: dict[str, Any]):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO research_orders (id, customer_email, request_json) VALUES (?, ?, ?)",
            (order_id, email, json.dumps(request_data, ensure_ascii=False)),
        )

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
            """UPDATE research_orders SET status='generation_failed', updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND status='generating'""",
            (order_id,),
        )
