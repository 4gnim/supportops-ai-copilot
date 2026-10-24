import sqlite3
from pathlib import Path

from supportops.config import settings


def _connect() -> sqlite3.Connection:
    db_path: Path = settings.feedback_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_feedback_db() -> None:
    connection = _connect()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def save_feedback(request_id: str, rating: int, comment: str | None) -> int:
    initialize_feedback_db()
    connection = _connect()
    try:
        cursor = connection.execute(
            "INSERT INTO feedback (request_id, rating, comment) VALUES (?, ?, ?)",
            (request_id, rating, comment),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()
