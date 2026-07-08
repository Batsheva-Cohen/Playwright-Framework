"""שכבת גישה לבסיס הנתונים - SQLite גולמי עם סכמה מפורשת.

נתיב ה-DB ניתן להגדרה דרך משתנה הסביבה TASKBOARD_DB. כך אפשר להריץ
מספר אינסטנסים של השרת מאחורי load balancer כשכולם חולקים את אותו קובץ DB.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_DB = Path(__file__).resolve().parent.parent / "tasks.db"
DB_PATH = Path(os.environ.get("TASKBOARD_DB", str(_DEFAULT_DB)))

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    status      TEXT    NOT NULL DEFAULT 'todo',
    priority    TEXT    NOT NULL DEFAULT 'medium',
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    content_encrypted TEXT    NOT NULL,
    created_at        TEXT    NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()