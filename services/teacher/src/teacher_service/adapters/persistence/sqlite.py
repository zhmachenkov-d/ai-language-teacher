"""SQLite persistence adapter for the Learner + LivingPlan store."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from teacher_service.domain.learner import (
    INTAKE_STEP_GREETING,
    Learner,
    WeeklySlot,
    validate_weekly_slot,
)
from teacher_service.domain.living_plan import (
    LessonRecord,
    LivingPlan,
    LivingPlanProjection,
    PathOption,
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
    placement_complete INTEGER NOT NULL DEFAULT 0,
    plan_complete INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS living_plan (
    id TEXT PRIMARY KEY NOT NULL,
    learner_id TEXT NOT NULL UNIQUE,
    goals_json TEXT NOT NULL,
    focus TEXT NOT NULL,
    upcoming_topics_json TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    selected_path_id TEXT NOT NULL,
    proposed_paths_json TEXT NOT NULL,
    revisable INTEGER NOT NULL DEFAULT 1,
    target_language TEXT NOT NULL,
    l1 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lesson_record (
    id TEXT PRIMARY KEY NOT NULL,
    living_plan_id TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    timezone TEXT NOT NULL,
    FOREIGN KEY (living_plan_id) REFERENCES living_plan(id)
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

_PLAN_COLUMNS: tuple[tuple[str, str], ...] = (
    ("plan_complete", "INTEGER NOT NULL DEFAULT 0"),
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
    "placement_speaking_score, placement_complete, plan_complete"
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


def _dumps_paths(paths: tuple[PathOption, ...]) -> str:
    return json.dumps(
        [
            {
                "id": p.id,
                "title": p.title,
                "summary": p.summary,
                "recommended": p.recommended,
            }
            for p in paths
        ],
        ensure_ascii=False,
    )


def _loads_paths(raw: str | None) -> tuple[PathOption, ...]:
    """Parse persisted proposed_paths; raise ValueError on corrupt data.

    Callers map this to `plan_inconsistent` — never return truncated/empty paths.
    """
    if not raw:
        raise ValueError("proposed_paths_json is missing or empty")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("proposed_paths_json is not valid JSON") from exc
    if not isinstance(data, list):
        raise ValueError("proposed_paths_json must be a JSON array")
    if not data:
        raise ValueError("proposed_paths_json is an empty array")
    out: list[PathOption] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"proposed_paths[{i}] must be an object")
        path_id = item.get("id")
        title = item.get("title")
        summary = item.get("summary")
        recommended = item.get("recommended")
        if (
            not isinstance(path_id, str)
            or not isinstance(title, str)
            or not isinstance(summary, str)
            or not isinstance(recommended, bool)
        ):
            raise ValueError(
                f"proposed_paths[{i}] must have string id/title/summary "
                "and boolean recommended"
            )
        out.append(
            PathOption(
                id=path_id,
                title=title,
                summary=summary,
                recommended=recommended,
            )
        )
    return tuple(out)


def _utc_iso(value: datetime) -> str:
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc_iso(raw: str) -> datetime:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"unparseable scheduled_at: {raw!r}")
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"unparseable scheduled_at: {raw!r}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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
        plan_complete=_bool_from_row(row, keys, "plan_complete"),
    )


def _row_to_living_plan(row: sqlite3.Row) -> LivingPlan:
    return LivingPlan(
        id=row["id"],
        learner_id=row["learner_id"],
        goals=_loads_str_list(row["goals_json"]),
        focus=row["focus"],
        upcoming_topics=_loads_str_list(row["upcoming_topics_json"]),
        difficulty=row["difficulty"],
        selected_path_id=row["selected_path_id"],
        proposed_paths=_loads_paths(row["proposed_paths_json"]),
        revisable=bool(row["revisable"]),
        target_language=row["target_language"],
        l1=row["l1"],
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
        # Schema declares FKs (e.g. lesson_record → living_plan); SQLite off by default.
        conn.execute("PRAGMA foreign_keys=ON")
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
                *_PLAN_COLUMNS,
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
                "placement_complete, plan_complete"
                ") VALUES ("
                "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
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
                    int(learner.plan_complete),
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
                "placement_complete = ?, plan_complete = ? "
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
                    int(learner.plan_complete),
                    learner.id,
                ),
            )
            conn.commit()
        return learner

    def create_living_plan_atomic(
        self,
        plan: LivingPlan,
        lessons: tuple[LessonRecord, ...],
    ) -> LivingPlanProjection:
        with self._connect() as conn:
            try:
                conn.execute("BEGIN")
                conn.execute(
                    "INSERT INTO living_plan ("
                    "id, learner_id, goals_json, focus, upcoming_topics_json, "
                    "difficulty, selected_path_id, proposed_paths_json, revisable, "
                    "target_language, l1"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        plan.id,
                        plan.learner_id,
                        _dumps_str_list(plan.goals),
                        plan.focus,
                        _dumps_str_list(plan.upcoming_topics),
                        plan.difficulty,
                        plan.selected_path_id,
                        _dumps_paths(plan.proposed_paths),
                        int(plan.revisable),
                        plan.target_language,
                        plan.l1,
                    ),
                )
                for lesson in lessons:
                    conn.execute(
                        "INSERT INTO lesson_record ("
                        "id, living_plan_id, scheduled_at, timezone"
                        ") VALUES (?, ?, ?, ?)",
                        (
                            lesson.id,
                            lesson.living_plan_id,
                            _utc_iso(lesson.scheduled_at),
                            lesson.timezone,
                        ),
                    )
                updated = conn.execute(
                    "UPDATE learner SET plan_complete = 1 WHERE id = ?",
                    (plan.learner_id,),
                )
                if updated.rowcount != 1:
                    raise ValueError("learner not found for living plan")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return LivingPlanProjection(plan=plan, lessons=lessons)

    def load_living_plan(self, learner_id: str) -> LivingPlanProjection | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, learner_id, goals_json, focus, upcoming_topics_json, "
                "difficulty, selected_path_id, proposed_paths_json, revisable, "
                "target_language, l1 FROM living_plan WHERE learner_id = ?",
                (learner_id,),
            ).fetchone()
            if row is None:
                return None
            plan = _row_to_living_plan(row)
            lesson_rows = conn.execute(
                "SELECT id, living_plan_id, scheduled_at, timezone "
                "FROM lesson_record WHERE living_plan_id = ? "
                "ORDER BY scheduled_at ASC",
                (plan.id,),
            ).fetchall()
        lessons = tuple(
            LessonRecord(
                id=r["id"],
                living_plan_id=r["living_plan_id"],
                scheduled_at=_parse_utc_iso(r["scheduled_at"]),
                timezone=r["timezone"],
            )
            for r in lesson_rows
        )
        return LivingPlanProjection(plan=plan, lessons=lessons)
