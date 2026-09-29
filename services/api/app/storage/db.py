"""SQLite storage for diagnosis history and the feedback loop (plan item #15:
ask the farmer later whether it actually helped)."""
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.environ.get("AGROSENTINEL_DB_PATH", os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "agrosentinel.db"
))


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS diagnoses (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                crop TEXT NOT NULL,
                result_json TEXT NOT NULL,
                farmer_feedback_status TEXT DEFAULT 'pending'
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                diagnosis_id TEXT NOT NULL REFERENCES diagnoses(id),
                created_at TEXT NOT NULL,
                improved INTEGER,
                notes TEXT
            )
        """)


def save_diagnosis(crop: str, result: dict) -> str:
    diagnosis_id = str(uuid.uuid4())
    with _conn() as c:
        c.execute(
            "INSERT INTO diagnoses (id, created_at, crop, result_json) VALUES (?, ?, ?, ?)",
            (diagnosis_id, datetime.now(timezone.utc).isoformat(), crop, json.dumps(result)),
        )
    return diagnosis_id


def list_history(limit: int = 50) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, created_at, crop, result_json, farmer_feedback_status "
            "FROM diagnoses ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [
        {"id": r["id"], "created_at": r["created_at"], "crop": r["crop"],
         "result": json.loads(r["result_json"]), "feedback_status": r["farmer_feedback_status"]}
        for r in rows
    ]


def submit_feedback(diagnosis_id: str, improved: bool | None, notes: str = "") -> dict:
    with _conn() as c:
        exists = c.execute("SELECT 1 FROM diagnoses WHERE id = ?", (diagnosis_id,)).fetchone()
        if not exists:
            return {"ok": False, "reason": "unknown diagnosis_id"}
        c.execute(
            "INSERT INTO feedback (id, diagnosis_id, created_at, improved, notes) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), diagnosis_id, datetime.now(timezone.utc).isoformat(),
             None if improved is None else int(improved), notes),
        )
        c.execute("UPDATE diagnoses SET farmer_feedback_status = 'received' WHERE id = ?", (diagnosis_id,))
    return {"ok": True}
