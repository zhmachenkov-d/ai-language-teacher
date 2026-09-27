"""SQLite persistence adapter for the Learner store."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from teacher_service.domain.learner import Learner

_SCHEMA = """
CREATE TABLE IF NOT EXISTS learner (
    id TEXT PRIMARY KEY NOT NULL,
    target_language TEXT NOT NULL,
    l1 TEXT NOT NULL,
    timezone TEXT NOT NULL
);
"""


class SqliteStore:
    """PersistencePort implementation backed by stdlib sqlite3."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
            conn.commit()

    def create_learner(self, learner: Learner) -> Learner:
        with self._connect() as conn:
            existing = conn.execute("SELECT id FROM learner LIMIT 1").fetchone()
            if existing is not None:
                raise ValueError("learner already exists; v1 is single-learner")
            conn.execute(
                "INSERT INTO learner (id, target_language, l1, timezone) "
                "VALUES (?, ?, ?, ?)",
                (
                    learner.id,
                    learner.target_language,
                    learner.l1,
                    learner.timezone,
                ),
            )
            conn.commit()
        return learner

    def load_learner(self) -> Learner | None:
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM learner").fetchone()[0]
            if count > 1:
                raise RuntimeError(
                    f"expected at most one learner row, found {count}"
                )
            row = conn.execute(
                "SELECT id, target_language, l1, timezone FROM learner LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        return Learner(
            id=row["id"],
            target_language=row["target_language"],
            l1=row["l1"],
            timezone=row["timezone"],
        )
