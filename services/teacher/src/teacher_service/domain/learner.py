"""Learner entity and intake get-or-create / update use cases (via PersistencePort)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Sequence

if TYPE_CHECKING:
    from teacher_service.ports.persistence import PersistencePort

DEFAULT_TARGET_LANGUAGE = "en"
DEFAULT_L1 = "ru"
DEFAULT_TIMEZONE = "UTC"

INTAKE_STEP_GREETING = "greeting"
INTAKE_STEP_GOALS = "goals"
INTAKE_STEP_INTERESTS = "interests"
INTAKE_STEP_DURATION = "duration"
INTAKE_STEP_SCHEDULE = "schedule"
INTAKE_STEP_COMPLETE = "complete"

INTAKE_STEPS: tuple[str, ...] = (
    INTAKE_STEP_GREETING,
    INTAKE_STEP_GOALS,
    INTAKE_STEP_INTERESTS,
    INTAKE_STEP_DURATION,
    INTAKE_STEP_SCHEDULE,
    INTAKE_STEP_COMPLETE,
)

ALLOWED_LESSON_DURATIONS: frozenset[int] = frozenset({30, 45, 60})

# Sentinel: keyword omitted from update_learner → leave field unchanged.
_UNSET: Any = object()


@dataclass(frozen=True)
class WeeklySlot:
    """One weekly lesson slot in the learner's local timezone."""

    weekday: int  # ISO: 0=Monday … 6=Sunday
    start_minute: int  # minutes from local midnight, 0–1439


@dataclass(frozen=True)
class Learner:
    """Learner profile persisted in SQLite (prefs + intake progress)."""

    id: str
    target_language: str
    l1: str
    timezone: str
    address_as: str | None = None
    age: int | None = None
    goals: tuple[str, ...] = ()
    desired_outcome: tuple[str, ...] = ()
    interests: tuple[str, ...] = ()
    emphasis: tuple[str, ...] = ()
    lesson_duration_minutes: int | None = None
    weekly_slots: tuple[WeeklySlot, ...] = ()
    intake_step: str = INTAKE_STEP_GREETING


def _coerce_str_list(value: Sequence[str]) -> tuple[str, ...]:
    return tuple(str(item) for item in value)


def coalesce_weekly_slots(slots: Sequence[WeeklySlot]) -> tuple[WeeklySlot, ...]:
    """Drop duplicate (weekday, start_minute) pairs; preserve first-seen order."""
    seen: set[tuple[int, int]] = set()
    out: list[WeeklySlot] = []
    for slot in slots:
        key = (slot.weekday, slot.start_minute)
        if key in seen:
            continue
        seen.add(key)
        out.append(slot)
    return tuple(out)


def validate_weekly_slot(slot: WeeklySlot) -> None:
    if (
        isinstance(slot.weekday, bool)
        or not isinstance(slot.weekday, int)
        or not (0 <= slot.weekday <= 6)
    ):
        raise ValueError("weekday must be an integer 0–6 (Mon–Sun)")
    if (
        isinstance(slot.start_minute, bool)
        or not isinstance(slot.start_minute, int)
        or not (0 <= slot.start_minute <= 1439)
    ):
        raise ValueError("start_minute must be an integer 0–1439")


def _require_intake_complete(learner: Learner) -> None:
    """Reject intake_step=complete unless STEP_COMPLETE fields are present."""
    if not learner.address_as or not str(learner.address_as).strip():
        raise ValueError("address_as is required before intake complete")
    if (
        not isinstance(learner.age, int)
        or isinstance(learner.age, bool)
        or not (1 <= learner.age <= 120)
    ):
        raise ValueError("age 1–120 is required before intake complete")
    for name, values in (
        ("goals", learner.goals),
        ("desired_outcome", learner.desired_outcome),
        ("interests", learner.interests),
        ("emphasis", learner.emphasis),
    ):
        if not values:
            raise ValueError(f"{name} must be non-empty before intake complete")
    if learner.lesson_duration_minutes not in ALLOWED_LESSON_DURATIONS:
        raise ValueError(
            "lesson_duration_minutes must be 30, 45, or 60 before intake complete"
        )
    if not learner.timezone or not learner.timezone.strip():
        raise ValueError("timezone is required before intake complete")
    if not learner.weekly_slots:
        raise ValueError(
            "weekly_slots must contain at least one slot before intake complete"
        )


def get_or_create_learner(store: PersistencePort) -> Learner:
    """Return the existing Learner or create one with v1 defaults."""
    existing = store.load_learner()
    if existing is not None:
        return existing
    learner = Learner(
        id=str(uuid.uuid4()),
        target_language=DEFAULT_TARGET_LANGUAGE,
        l1=DEFAULT_L1,
        timezone=DEFAULT_TIMEZONE,
    )
    return store.create_learner(learner)


def update_learner(
    store: PersistencePort,
    *,
    address_as: Any = _UNSET,
    age: Any = _UNSET,
    goals: Any = _UNSET,
    desired_outcome: Any = _UNSET,
    interests: Any = _UNSET,
    emphasis: Any = _UNSET,
    lesson_duration_minutes: Any = _UNSET,
    timezone: Any = _UNSET,
    weekly_slots: Any = _UNSET,
    intake_step: Any = _UNSET,
) -> Learner:
    """Patch the single Learner. Omitted kwargs leave the current value unchanged."""
    current = get_or_create_learner(store)
    updates: dict[str, Any] = {}

    if address_as is not _UNSET:
        if not isinstance(address_as, str) or not address_as.strip():
            raise ValueError("address_as must be a non-empty string")
        updates["address_as"] = address_as.strip()

    if age is not _UNSET:
        if not isinstance(age, int) or isinstance(age, bool) or not (1 <= age <= 120):
            raise ValueError("age must be an integer 1–120")
        updates["age"] = age

    if goals is not _UNSET:
        if not isinstance(goals, (list, tuple)):
            raise ValueError("goals must be a list of strings")
        updates["goals"] = _coerce_str_list(goals)
    if desired_outcome is not _UNSET:
        if not isinstance(desired_outcome, (list, tuple)):
            raise ValueError("desired_outcome must be a list of strings")
        updates["desired_outcome"] = _coerce_str_list(desired_outcome)
    if interests is not _UNSET:
        if not isinstance(interests, (list, tuple)):
            raise ValueError("interests must be a list of strings")
        updates["interests"] = _coerce_str_list(interests)
    if emphasis is not _UNSET:
        if not isinstance(emphasis, (list, tuple)):
            raise ValueError("emphasis must be a list of strings")
        updates["emphasis"] = _coerce_str_list(emphasis)

    if lesson_duration_minutes is not _UNSET:
        if lesson_duration_minutes not in ALLOWED_LESSON_DURATIONS:
            raise ValueError("lesson_duration_minutes must be 30, 45, or 60")
        updates["lesson_duration_minutes"] = lesson_duration_minutes

    if timezone is not _UNSET:
        if not isinstance(timezone, str) or not timezone.strip():
            raise ValueError("timezone must be a non-empty string")
        updates["timezone"] = timezone.strip()

    if weekly_slots is not _UNSET:
        if not isinstance(weekly_slots, (list, tuple)):
            raise ValueError("weekly_slots must be a list")
        for slot in weekly_slots:
            if not isinstance(slot, WeeklySlot):
                raise ValueError("weekly_slots items must be WeeklySlot")
            validate_weekly_slot(slot)
        updates["weekly_slots"] = coalesce_weekly_slots(weekly_slots)

    if intake_step is not _UNSET:
        if intake_step not in INTAKE_STEPS:
            raise ValueError(f"intake_step must be one of {INTAKE_STEPS}")
        updates["intake_step"] = intake_step

    if not updates:
        return current
    updated = replace(current, **updates)
    if updated.intake_step == INTAKE_STEP_COMPLETE:
        _require_intake_complete(updated)
    return store.update_learner(updated)
