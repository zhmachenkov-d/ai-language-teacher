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
from teacher_service.domain.placement import (
    PLACEMENT_STAGE_BRIEFING,
    PLACEMENT_STAGES,
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
    intake_step TEXT NOT NULL DEFAULT 'greeting',
    consent_mic INTEGER NOT NULL DEFAULT 0,
    consent_telegram INTEGER NOT NULL DEFAULT 0,
    consent_ai INTEGER NOT NULL DEFAULT 0,
    consent_privacy INTEGER NOT NULL DEFAULT 0,
    consent_complete INTEGER NOT NULL DEFAULT 0,
    placement_stage TEXT NOT NULL DEFAULT 'briefing',
    placement_items_json TEXT,
    placement_written_answers_json TEXT NOT NULL DEFAULT '[]',
    placement_written_score REAL,
    placement_listening_generated INTEGER NOT NULL DEFAULT 0,
    placement_listening_played INTEGER NOT NULL DEFAULT 0,
    placement_listening_answers_json TEXT NOT NULL DEFAULT '[]',
    placement_listening_score REAL,
    placement_speaking_transcript TEXT,
    placement_speaking_score REAL,
    placement_complete INTEGER NOT NULL DEFAULT 0
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

_CONSENT_COLUMNS: tuple[tuple[str, str], ...] = (
    ("consent_mic", "INTEGER NOT NULL DEFAULT 0"),
    ("consent_telegram", "INTEGER NOT NULL DEFAULT 0"),
    ("consent_ai", "INTEGER NOT NULL DEFAULT 0"),
    ("consent_privacy", "INTEGER NOT NULL DEFAULT 0"),
    ("consent_complete", "INTEGER NOT NULL DEFAULT 0"),
)

_PLACEMENT_COLUMNS: tuple[tuple[str, str], ...] = (
    ("placement_stage", "TEXT NOT NULL DEFAULT 'briefing'"),
    ("placement_items_json", "TEXT"),
    ("placement_written_answers_json", "TEXT NOT NULL DEFAULT '[]'"),
    ("placement_written_score", "REAL"),
    ("placement_listening_generated", "INTEGER NOT NULL DEFAULT 0"),
    ("placement_listening_played", "INTEGER NOT NULL DEFAULT 0"),
    ("placement_listening_answers_json", "TEXT NOT NULL DEFAULT '[]'"),
    ("placement_listening_score", "REAL"),
    ("placement_speaking_transcript", "TEXT"),
    ("placement_speaking_score", "REAL"),
    ("placement_complete", "INTEGER NOT NULL DEFAULT 0"),
)

_SELECT_COLS = (
    "id, target_language, l1, timezone, address_as, age, "
    "goals_json, desired_outcome_json, interests_json, emphasis_json, "
    "lesson_duration_minutes, weekly_slots_json, intake_step, "
    "consent_mic, consent_telegram, consent_ai, consent_privacy, consent_complete, "
    "placement_stage, placement_items_json, placement_written_answers_json, "
    "placement_written_score, placement_listening_generated, "
    "placement_listening_played, placement_listening_answers_json, "
    "placement_listening_score, placement_speaking_transcript, "
    "placement_speaking_score, placement_complete"
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


def _dumps_int_list(values: tuple[int, ...]) -> str:
    return json.dumps(list(values))


def _loads_int_list(raw: str | None) -> tuple[int, ...]:
    if not raw:
        return ()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ()
    if not isinstance(data, list):
        return ()
    out: list[int] = []
    for item in data:
        if isinstance(item, bool) or not isinstance(item, int):
            continue
        out.append(item)
    return tuple(out)


def _dumps_dict_or_none(value: dict | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _loads_dict_or_none(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


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


def _bool_from_row(row: sqlite3.Row, keys: set[str], name: str) -> bool:
    if name not in keys:
        return False
    return bool(row[name])


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
        consent_mic=_bool_from_row(row, keys, "consent_mic"),
        consent_telegram=_bool_from_row(row, keys, "consent_telegram"),
        consent_ai=_bool_from_row(row, keys, "consent_ai"),
        consent_privacy=_bool_from_row(row, keys, "consent_privacy"),
        consent_complete=_bool_from_row(row, keys, "consent_complete"),
        placement_stage=(
            row["placement_stage"]
            if "placement_stage" in keys and row["placement_stage"] in PLACEMENT_STAGES
            else PLACEMENT_STAGE_BRIEFING
        ),
        placement_items=_loads_dict_or_none(
            row["placement_items_json"] if "placement_items_json" in keys else None
        ),
        placement_written_answers=_loads_int_list(
            row["placement_written_answers_json"]
            if "placement_written_answers_json" in keys
            else None
        ),
        placement_written_score=(
            row["placement_written_score"]
            if "placement_written_score" in keys
            else None
        ),
        placement_listening_generated=_bool_from_row(
            row, keys, "placement_listening_generated"
        ),
        placement_listening_played=_bool_from_row(
            row, keys, "placement_listening_played"
        ),
        placement_listening_answers=_loads_int_list(
            row["placement_listening_answers_json"]
            if "placement_listening_answers_json" in keys
            else None
        ),
        placement_listening_score=(
            row["placement_listening_score"]
            if "placement_listening_score" in keys
            else None
        ),
        placement_speaking_transcript=(
            row["placement_speaking_transcript"]
            if "placement_speaking_transcript" in keys
            else None
        ),
        placement_speaking_score=(
            row["placement_speaking_score"]
            if "placement_speaking_score" in keys
            else None
        ),
        placement_complete=_bool_from_row(row, keys, "placement_complete"),
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
                row[1] for row in conn.execute("PRAGMA table_info(learner)").fetchall()
            }
            for name, decl in (
                *_INTAKE_COLUMNS,
                *_CONSENT_COLUMNS,
                *_PLACEMENT_COLUMNS,
            ):
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
                "lesson_duration_minutes, weekly_slots_json, intake_step, "
                "consent_mic, consent_telegram, consent_ai, consent_privacy, "
                "consent_complete, "
                "placement_stage, placement_items_json, "
                "placement_written_answers_json, placement_written_score, "
                "placement_listening_generated, placement_listening_played, "
                "placement_listening_answers_json, placement_listening_score, "
                "placement_speaking_transcript, placement_speaking_score, "
                "placement_complete"
                ") VALUES ("
                "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
                ")",
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
                    int(learner.consent_mic),
                    int(learner.consent_telegram),
                    int(learner.consent_ai),
                    int(learner.consent_privacy),
                    int(learner.consent_complete),
                    learner.placement_stage,
                    _dumps_dict_or_none(learner.placement_items),
                    _dumps_int_list(learner.placement_written_answers),
                    learner.placement_written_score,
                    int(learner.placement_listening_generated),
                    int(learner.placement_listening_played),
                    _dumps_int_list(learner.placement_listening_answers),
                    learner.placement_listening_score,
                    learner.placement_speaking_transcript,
                    learner.placement_speaking_score,
                    int(learner.placement_complete),
                ),
            )
            conn.commit()
        return learner

    def load_learner(self) -> Learner | None:
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM learner").fetchone()[0]
            if count > 1:
                raise RuntimeError(f"expected at most one learner row, found {count}")
            row = conn.execute(f"SELECT {_SELECT_COLS} FROM learner LIMIT 1").fetchone()
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
                "intake_step = ?, "
                "consent_mic = ?, consent_telegram = ?, consent_ai = ?, "
                "consent_privacy = ?, consent_complete = ?, "
                "placement_stage = ?, placement_items_json = ?, "
                "placement_written_answers_json = ?, placement_written_score = ?, "
                "placement_listening_generated = ?, placement_listening_played = ?, "
                "placement_listening_answers_json = ?, placement_listening_score = ?, "
                "placement_speaking_transcript = ?, placement_speaking_score = ?, "
                "placement_complete = ? "
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
                    int(learner.consent_mic),
                    int(learner.consent_telegram),
                    int(learner.consent_ai),
                    int(learner.consent_privacy),
                    int(learner.consent_complete),
                    learner.placement_stage,
                    _dumps_dict_or_none(learner.placement_items),
                    _dumps_int_list(learner.placement_written_answers),
                    learner.placement_written_score,
                    int(learner.placement_listening_generated),
                    int(learner.placement_listening_played),
                    _dumps_int_list(learner.placement_listening_answers),
                    learner.placement_listening_score,
                    learner.placement_speaking_transcript,
                    learner.placement_speaking_score,
                    int(learner.placement_complete),
                    learner.id,
                ),
            )
            conn.commit()
        return learner
