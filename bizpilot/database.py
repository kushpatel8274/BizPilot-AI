"""SQLite persistence for approved BizPilot data."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Draft:
    kind: str
    title: str
    content: str


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    initialize(conn)
    return conn


def initialize(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def save_draft(conn: sqlite3.Connection, draft: Draft) -> int:
    if not draft.kind.strip() or not draft.title.strip() or not draft.content.strip():
        raise ValueError("Draft kind, title, and content are required before saving.")
    cursor = conn.execute(
        "INSERT INTO drafts (kind, title, content) VALUES (?, ?, ?)",
        (draft.kind.strip(), draft.title.strip(), draft.content.strip()),
    )
    conn.commit()
    return int(cursor.lastrowid)


def list_drafts(conn: sqlite3.Connection, limit: int = 20) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, kind, title, content, created_at FROM drafts ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
