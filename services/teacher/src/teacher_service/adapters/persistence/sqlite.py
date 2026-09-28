"""SQLite persistence adapter for the Learner store."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from teacher_service.domain.learner import (
    INTAKE_STEP_GREETING,
    Learner,
    WeeklySlot,
    validate_weekly_slot,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS learner (
    id TEXT PRIMARY KEY NOT NULL,
    target_language TEXT NOT NULL,
    l1 TEXT NOT NULL,
    timezone TEXT NOT NULL,
    address_as TEXT,
    age INTEGER,
    goals_json TEXT NOT NULL DEFAULT '[]',
    desired_outcome_json TEXT NOT NULL DEFAULT '[]',
    interests_json TEXT NOT NULL DEFAULT '[]',
    emphasis_json TEXT NOT NULL DEFAULT '[]',
    lesson_duration_minutes INTEGER,
    weekly_slots_json TEXT NOT NULL DEFAULT '[]',
    intake_step TEXT NOT NULL DEFAULT 'greeting'
);
"""

_INTAKE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("address_as", "TEXT"),
    ("age", "INTEGER"),
    ("goals_json", "TEXT NOT NULL DEFAULT '[]'"),
    ("desired_outcome_json", "TEXT NOT NULL DEFAULT '[]'"),
    ("interests_json", "TEXT NOT NULL DEFAULT '[]'"),
    ("emphasis_json", "TEXT NOT NULL DEFAULT '[]'"),
    ("lesson_duration_minutes", "INTEGER"),
    ("weekly_slots_json", "TEXT NOT NULL DEFAULT '[]'"),
    ("intake_step", "TEXT NOT NULL DEFAULT 'greeting'"),
)

_SELECT_COLS = (
    "id, target_language, l1, timezone, address_as, age, "
    "goals_json, desired_outcome_json, interests_json, emphasis_json, "
    "lesson_duration_minutes, weekly_slots_json, intake_step"
)


def _dumps_str_list(values: tuple[str, ...]) -> str:
    return json.dumps(list(values), ensure_ascii=False)


def _loads_str_list(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ()
    if not isinstance(data, list):
        return ()
    return tuple(str(item) for item in data)


def _dumps_slots(slots: tuple[WeeklySlot, ...]) -> str:
    return json.dumps(
        [{"weekday": s.weekday, "start_minute": s.start_minute} for s in slots],
        ensure_ascii=False,
    )


def _loads_slots(raw: str | None) -> tuple[WeeklySlot, ...]:
    if not raw:
        return ()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ()
    if not isinstance(data, list):
        return ()
    out: list[WeeklySlot] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if "weekday" not in item or "start_minute" not in item:
            continue
        if isinstance(item["weekday"], bool) or isinstance(item["start_minute"], bool):
            continue
        try:
            slot = WeeklySlot(
                weekday=int(item["weekday"]),
                start_minute=int(item["start_minute"]),
            )
            validate_weekly_slot(slot)
        except (TypeError, ValueError):
            continue
        out.append(slot)
    return tuple(out)


def _row_to_learner(row: sqlite3.Row) -> Learner:
    keys = set(row.keys())
    return Learner(
        id=row["id"],
        target_language=row["target_language"],
        l1=row["l1"],
        timezone=row["timezone"],
        address_as=row["address_as"] if "address_as" in keys else None,
        age=row["age"] if "age" in keys else None,
        goals=_loads_str_list(row["goals_json"] if "goals_json" in keys else None),
        desired_outcome=_loads_str_list(
            row["desired_outcome_json"] if "desired_outcome_json" in keys else None
        ),
        interests=_loads_str_list(
            row["interests_json"] if "interests_json" in keys else None
        ),
        emphasis=_loads_str_list(
            row["emphasis_json"] if "emphasis_json" in keys else None
        ),
        lesson_duration_minutes=(
            row["lesson_duration_minutes"]
            if "lesson_duration_minutes" in keys
            else None
        ),
        weekly_slots=_loads_slots(
            row["weekly_slots_json"] if "weekly_slots_json" in keys else None
        ),
        intake_step=(
            row["intake_step"]
            if "intake_step" in keys and row["intake_step"]
            else INTAKE_STEP_GREETING
        ),
    )


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
            existing = {
                row[1]
                for row in conn.execute("PRAGMA table_info(learner)").fetchall()
            }
            for name, decl in _INTAKE_COLUMNS:
                if name not in existing:
                    conn.execute(f"ALTER TABLE learner ADD COLUMN {name} {decl}")
            conn.commit()

    def create_learner(self, learner: Learner) -> Learner:
        with self._connect() as conn:
            existing = conn.execute("SELECT id FROM learner LIMIT 1").fetchone()
            if existing is not None:
                raise ValueError("learner already exists; v1 is single-learner")
            conn.execute(
                "INSERT INTO learner ("
                "id, target_language, l1, timezone, address_as, age, "
                "goals_json, desired_outcome_json, interests_json, emphasis_json, "
                "lesson_duration_minutes, weekly_slots_json, intake_step"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    learner.id,
                    learner.target_language,
                    learner.l1,
                    learner.timezone,
                    learner.address_as,
                    learner.age,
                    _dumps_str_list(learner.goals),
                    _dumps_str_list(learner.desired_outcome),
                    _dumps_str_list(learner.interests),
                    _dumps_str_list(learner.emphasis),
                    learner.lesson_duration_minutes,
                    _dumps_slots(learner.weekly_slots),
                    learner.intake_step,
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
                f"SELECT {_SELECT_COLS} FROM learner LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        return _row_to_learner(row)

    def update_learner(self, learner: Learner) -> Learner:
        with self._connect() as conn:
            existing = conn.execute("SELECT id FROM learner LIMIT 1").fetchone()
            if existing is None:
                raise ValueError("no learner to update")
            if existing["id"] != learner.id:
                raise ValueError("learner id mismatch")
            conn.execute(
                "UPDATE learner SET "
                "target_language = ?, l1 = ?, timezone = ?, "
                "address_as = ?, age = ?, "
                "goals_json = ?, desired_outcome_json = ?, "
                "interests_json = ?, emphasis_json = ?, "
                "lesson_duration_minutes = ?, weekly_slots_json = ?, "
                "intake_step = ? "
                "WHERE id = ?",
                (
                    learner.target_language,
                    learner.l1,
                    learner.timezone,
                    learner.address_as,
                    learner.age,
                    _dumps_str_list(learner.goals),
                    _dumps_str_list(learner.desired_outcome),
                    _dumps_str_list(learner.interests),
                    _dumps_str_list(learner.emphasis),
                    learner.lesson_duration_minutes,
                    _dumps_slots(learner.weekly_slots),
                    learner.intake_step,
                    learner.id,
                ),
            )
            conn.commit()
        return learner
