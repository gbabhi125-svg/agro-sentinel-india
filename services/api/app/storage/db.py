"""
SQLite storage for:
- diagnosis history + the feedback loop (farmer says later whether it helped)
- photo history per plant label, for weekly progress tracking (medium
  addition #8) — photos are saved to disk under PHOTO_DIR, only the path is
  stored in the DB
- opt-in community pest/disease reports (medium addition #9) — a diagnosis
  is only added here if the farmer explicitly opts in when submitting it
"""
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.environ.get("AGROSENTINEL_DB_PATH", os.path.join(BASE_DIR, "agrosentinel.db"))
PHOTO_DIR = os.environ.get("AGROSENTINEL_PHOTO_DIR", os.path.join(BASE_DIR, "data", "photos"))
os.makedirs(PHOTO_DIR, exist_ok=True)


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _add_column_if_missing(c, table: str, column: str, decl: str):
    cols = [r["name"] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


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
        _add_column_if_missing(c, "diagnoses", "plant_label", "TEXT")
        _add_column_if_missing(c, "diagnoses", "state", "TEXT")
        _add_column_if_missing(c, "diagnoses", "photo_path", "TEXT")

        c.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                diagnosis_id TEXT NOT NULL REFERENCES diagnoses(id),
                created_at TEXT NOT NULL,
                improved INTEGER,
                notes TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS alert_subscriptions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                device_token TEXT NOT NULL,
                state TEXT NOT NULL,
                crop TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS community_reports (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                state TEXT NOT NULL,
                crop TEXT NOT NULL,
                cause_id TEXT NOT NULL,
                cause_name TEXT NOT NULL
            )
        """)


def save_diagnosis(crop: str, result: dict, plant_label: str | None = None,
                    state: str | None = None, photo_bytes: bytes | None = None,
                    opt_in_community: bool = False) -> str:
    diagnosis_id = str(uuid.uuid4())
    photo_path = None
    if photo_bytes:
        photo_path = os.path.join(PHOTO_DIR, f"{diagnosis_id}.jpg")
        with open(photo_path, "wb") as f:
            f.write(photo_bytes)

    with _conn() as c:
        c.execute(
            "INSERT INTO diagnoses (id, created_at, crop, result_json, plant_label, state, photo_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (diagnosis_id, datetime.now(timezone.utc).isoformat(), crop, json.dumps(result),
             plant_label, state, photo_path),
        )
        if opt_in_community and state and result.get("status") == "diagnosed":
            c.execute(
                "INSERT INTO community_reports (id, created_at, state, crop, cause_id, cause_name) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), datetime.now(timezone.utc).isoformat(), state, crop,
                 result["cause_id"], result.get("specific_name") or result["cause_name"]),
            )
    return diagnosis_id


def list_history(limit: int = 50) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, created_at, crop, result_json, farmer_feedback_status, plant_label, photo_path "
            "FROM diagnoses ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [
        {"id": r["id"], "created_at": r["created_at"], "crop": r["crop"],
         "result": json.loads(r["result_json"]), "feedback_status": r["farmer_feedback_status"],
         "plant_label": r["plant_label"], "has_photo": bool(r["photo_path"])}
        for r in rows
    ]


def get_diagnosis(diagnosis_id: str) -> dict | None:
    with _conn() as c:
        r = c.execute("SELECT * FROM diagnoses WHERE id = ?", (diagnosis_id,)).fetchone()
    if not r:
        return None
    return {"id": r["id"], "created_at": r["created_at"], "crop": r["crop"],
            "result": json.loads(r["result_json"]), "plant_label": r["plant_label"],
            "state": r["state"], "photo_path": r["photo_path"]}


def get_photo_path(diagnosis_id: str) -> str | None:
    row = get_diagnosis(diagnosis_id)
    return row["photo_path"] if row and row["photo_path"] and os.path.exists(row["photo_path"]) else None


def list_plant_labels() -> list[str]:
    with _conn() as c:
        rows = c.execute(
            "SELECT DISTINCT plant_label FROM diagnoses WHERE plant_label IS NOT NULL ORDER BY plant_label"
        ).fetchall()
    return [r["plant_label"] for r in rows]


def photo_progress(plant_label: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, created_at, result_json, photo_path FROM diagnoses "
            "WHERE plant_label = ? AND photo_path IS NOT NULL ORDER BY created_at ASC",
            (plant_label,),
        ).fetchall()
    return [
        {"id": r["id"], "created_at": r["created_at"], "result": json.loads(r["result_json"]),
         "has_photo": True}
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


def community_alerts(state: str, crop: str, window_days: int = 14) -> list[dict]:
    """Opt-in reports only — plan item #9. Farmers must have ticked 'share with
    nearby farmers' when they submitted their diagnosis (see routers/doctor.py)."""
    since = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
    with _conn() as c:
        rows = c.execute(
            "SELECT cause_name, COUNT(*) as n FROM community_reports "
            "WHERE state = ? AND crop = ? AND created_at >= ? GROUP BY cause_name ORDER BY n DESC",
            (state, crop, since),
        ).fetchall()
    return [{"cause_name": r["cause_name"], "report_count": r["n"]} for r in rows]


def subscribe_alert(device_token: str, state: str, crop: str) -> str:
    sub_id = str(uuid.uuid4())
    with _conn() as c:
        c.execute(
            "INSERT INTO alert_subscriptions (id, created_at, device_token, state, crop) VALUES (?, ?, ?, ?, ?)",
            (sub_id, datetime.now(timezone.utc).isoformat(), device_token, state, crop),
        )
    return sub_id


def tokens_for(state: str, crop: str) -> list[str]:
    with _conn() as c:
        rows = c.execute(
            "SELECT DISTINCT device_token FROM alert_subscriptions WHERE state = ? AND crop = ?", (state, crop)
        ).fetchall()
    return [r["device_token"] for r in rows]


def officer_summary(days: int = 30) -> dict:
    """Aggregated, anonymised view for an agriculture officer — plan item #13.
    No per-farmer identity is stored anywhere in this schema, so there is
    nothing to redact: it was never collected."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with _conn() as c:
        by_cause = c.execute(
            "SELECT json_extract(result_json, '$.cause_name') as cause, COUNT(*) as n "
            "FROM diagnoses WHERE created_at >= ? AND json_extract(result_json, '$.status') = 'diagnosed' "
            "GROUP BY cause ORDER BY n DESC LIMIT 10", (since,)
        ).fetchall()
        by_state = c.execute(
            "SELECT state, COUNT(*) as n FROM diagnoses WHERE created_at >= ? AND state IS NOT NULL "
            "GROUP BY state ORDER BY n DESC LIMIT 15", (since,)
        ).fetchall()
        total = c.execute("SELECT COUNT(*) as n FROM diagnoses WHERE created_at >= ?", (since,)).fetchone()["n"]
        uncertain = c.execute(
            "SELECT COUNT(*) as n FROM diagnoses WHERE created_at >= ? "
            "AND json_extract(result_json, '$.status') = 'uncertain'", (since,)
        ).fetchone()["n"]
    return {
        "window_days": days, "total_diagnoses": total, "uncertain_count": uncertain,
        "top_causes": [{"cause": r["cause"], "count": r["n"]} for r in by_cause],
        "by_state": [{"state": r["state"], "count": r["n"]} for r in by_state],
    }
