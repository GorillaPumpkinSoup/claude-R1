import json
import sqlite3
from pathlib import Path


def get_connection(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            total_value REAL NOT NULL,
            payload TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def save_snapshot(conn: sqlite3.Connection, created_at: str, total_value: float, payload: dict) -> None:
    conn.execute(
        "INSERT INTO snapshots (created_at, total_value, payload) VALUES (?, ?, ?)",
        (created_at, total_value, json.dumps(payload, ensure_ascii=False, default=str)),
    )
    conn.commit()


def load_latest_snapshot(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute(
        "SELECT payload FROM snapshots ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return json.loads(row[0]) if row else None


def load_history(conn: sqlite3.Connection, limit: int = 200) -> list[dict]:
    rows = conn.execute(
        "SELECT payload FROM snapshots ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [json.loads(r[0]) for r in reversed(rows)]
