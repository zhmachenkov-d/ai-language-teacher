"""Learner entity and intake get-or-create / update use cases (via PersistencePort)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from teacher_service.domain.placement import (
    PLACEMENT_STAGE_BRIEFING,
    PLACEMENT_STAGE_COMPLETE,
    PLACEMENT_STAGE_LISTENING,
    PLACEMENT_STAGE_SPEAKING,
    PLACEMENT_STAGE_WRITTEN,
    PLACEMENT_STAGES,
    PlacementItemsError,
    parse_placement_items,
    score_choice_answers,
)

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
MIN_CONSENT_AGE = 16

# Sentinel: keyword omitted from update_learner → leave field unchanged.
_UNSET: Any = object()


class LearnerValidationError(ValueError):
    """Domain validation failure with a stable wire `code` for 422 envelopes."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class WeeklySlot:
    """One weekly lesson slot in the learner's local timezone."""

    weekday: int  # ISO: 0=Monday … 6=Sunday
    start_minute: int  # minutes from local midnight, 0–1439


@dataclass(frozen=True)
class Learner:
    """Learner profile persisted in SQLite (prefs + intake + consent)."""

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
    consent_mic: bool = False
    consent_telegram: bool = False
    consent_ai: bool = False
    consent_privacy: bool = False
    consent_complete: bool = False
    placement_stage: str = PLACEMENT_STAGE_BRIEFING
    placement_items: dict[str, Any] | None = None
    placement_written_answers: tuple[int, ...] = ()
    placement_written_score: float | None = None
    placement_listening_generated: bool = False
    placement_listening_played: bool = False
    placement_listening_answers: tuple[int, ...] = ()
    placement_listening_score: float | None = None
    placement_speaking_transcript: str | None = None
    placement_speaking_score: float | None = None
    placement_complete: bool = False
    plan_complete: bool = False


def _coerce_str_list(value: Sequence[str]) -> tuple[str, ...]:
    return tuple(str(item) for item in value)


def _coerce_bool(value: Any, *, field: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"{field} must be a boolean")


def _coerce_int_list(value: Any, *, field: str) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(v, int) and not isinstance(v, bool) for v in value
    ):
        raise ValueError(f"{field} must be a list of integers")
    return tuple(value)


def _placement_items_or_raise(raw_items: Any) -> Any:
    """Parse the persisted/incoming `placement_items` dict, or raise if absent/invalid."""
    if raw_items is None:
        raise ValueError("placement_items must be generated before submitting answers")
    try:
        return parse_placement_items(raw_items)
    except PlacementItemsError as exc:
        raise ValueError(str(exc)) from exc


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


def _require_consent_complete(learner: Learner) -> None:
    """Reject consent_complete=true unless intake done, age≥16, and required consents."""
    if learner.intake_step != INTAKE_STEP_COMPLETE:
        raise LearnerValidationError(
            "consent_before_intake",
            "consent_complete requires intake_step complete",
        )
    if (
        not isinstance(learner.age, int)
        or isinstance(learner.age, bool)
        or learner.age < MIN_CONSENT_AGE
    ):
        raise LearnerValidationError(
            "age_restricted",
            "consent_complete requires age 16 or older",
        )
    missing: list[str] = []
    if not learner.consent_mic:
        missing.append("consent_mic")
    if not learner.consent_ai:
        missing.append("consent_ai")
    if not learner.consent_privacy:
        missing.append("consent_privacy")
    if missing:
        raise LearnerValidationError(
            "consent_incomplete",
            "consent_complete requires " + ", ".join(missing),
        )


def _require_placement_prereqs(updated: Learner, *, up_to_stage: str) -> None:
    """Reject a placement stage/complete value unless earlier stage results are present.

    `up_to_stage` is the furthest stage being requested (READ from
    `updated.placement_stage`, or forced to `complete` for the explicit
    `placement_complete=True` gate) — mirrors 2.2's `_require_consent_complete`.
    """
    if up_to_stage == PLACEMENT_STAGE_BRIEFING:
        return
    if not updated.consent_complete:
        raise LearnerValidationError(
            "placement_requires_consent",
            "placement requires consent_complete",
        )
    if up_to_stage == PLACEMENT_STAGE_WRITTEN:
        return
    if updated.placement_written_score is None:
        raise LearnerValidationError(
            "placement_written_incomplete",
            "written result is required before advancing placement",
        )
    if up_to_stage == PLACEMENT_STAGE_LISTENING:
        return
    if (
        not updated.placement_listening_generated
        or not updated.placement_listening_played
        or updated.placement_listening_score is None
    ):
        raise LearnerValidationError(
            "placement_listening_incomplete",
            "listening result is required before advancing placement",
        )
    if up_to_stage == PLACEMENT_STAGE_SPEAKING:
        return
    transcript = updated.placement_speaking_transcript
    if (
        not isinstance(transcript, str)
        or not transcript.strip()
        or updated.placement_speaking_score is None
    ):
        raise LearnerValidationError(
            "placement_speaking_incomplete",
            "speaking result is required before placement_complete",
        )


def _require_placement_stage(updated: Learner) -> None:
    _require_placement_prereqs(updated, up_to_stage=updated.placement_stage)


def _require_placement_complete(updated: Learner) -> None:
    """Reject `placement_complete=true` unless listening+speaking are seedable.

    Checked regardless of the concurrent `placement_stage` value so a bare
    `PATCH {"placement_complete": true}` cannot bypass gaps (text-only complete
    matrix row) — mirrors 2.2's consent_complete FLAG rigor. Seedable speaking
    requires both a real STT transcript and a server-computed score.
    """
    _require_placement_prereqs(updated, up_to_stage=PLACEMENT_STAGE_COMPLETE)


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
    consent_mic: Any = _UNSET,
    consent_telegram: Any = _UNSET,
    consent_ai: Any = _UNSET,
    consent_privacy: Any = _UNSET,
    consent_complete: Any = _UNSET,
    placement_stage: Any = _UNSET,
    placement_items: Any = _UNSET,
    placement_written_answers: Any = _UNSET,
    placement_listening_generated: Any = _UNSET,
    placement_listening_played: Any = _UNSET,
    placement_listening_answers: Any = _UNSET,
    placement_speaking_transcript: Any = _UNSET,
    placement_speaking_score: Any = _UNSET,
    placement_complete: Any = _UNSET,
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

    if consent_mic is not _UNSET:
        updates["consent_mic"] = _coerce_bool(consent_mic, field="consent_mic")
    if consent_telegram is not _UNSET:
        updates["consent_telegram"] = _coerce_bool(
            consent_telegram, field="consent_telegram"
        )
    if consent_ai is not _UNSET:
        updates["consent_ai"] = _coerce_bool(consent_ai, field="consent_ai")
    if consent_privacy is not _UNSET:
        updates["consent_privacy"] = _coerce_bool(
            consent_privacy, field="consent_privacy"
        )
    if consent_complete is not _UNSET:
        updates["consent_complete"] = _coerce_bool(
            consent_complete, field="consent_complete"
        )

    if placement_stage is not _UNSET:
        if placement_stage not in PLACEMENT_STAGES:
            raise ValueError(f"placement_stage must be one of {PLACEMENT_STAGES}")
        updates["placement_stage"] = placement_stage

    if placement_items is not _UNSET:
        if not isinstance(placement_items, dict):
            raise ValueError("placement_items must be an object")
        updates["placement_items"] = placement_items

    if placement_written_answers is not _UNSET:
        answers = _coerce_int_list(
            placement_written_answers, field="placement_written_answers"
        )
        items = _placement_items_or_raise(
            placement_items
            if placement_items is not _UNSET
            else current.placement_items
        )
        try:
            score = score_choice_answers(items.written, answers)
        except ValueError as exc:
            raise ValueError(f"placement_written_answers: {exc}") from exc
        updates["placement_written_answers"] = answers
        updates["placement_written_score"] = score

    if placement_listening_generated is not _UNSET:
        updates["placement_listening_generated"] = _coerce_bool(
            placement_listening_generated, field="placement_listening_generated"
        )

    if placement_listening_played is not _UNSET:
        updates["placement_listening_played"] = _coerce_bool(
            placement_listening_played, field="placement_listening_played"
        )

    if placement_listening_answers is not _UNSET:
        answers = _coerce_int_list(
            placement_listening_answers, field="placement_listening_answers"
        )
        items = _placement_items_or_raise(
            placement_items
            if placement_items is not _UNSET
            else current.placement_items
        )
        try:
            score = score_choice_answers(items.listening.questions, answers)
        except ValueError as exc:
            raise ValueError(f"placement_listening_answers: {exc}") from exc
        updates["placement_listening_answers"] = answers
        updates["placement_listening_score"] = score

    if placement_speaking_transcript is not _UNSET:
        if (
            not isinstance(placement_speaking_transcript, str)
            or not placement_speaking_transcript.strip()
        ):
            raise ValueError("placement_speaking_transcript must be a non-empty string")
        updates["placement_speaking_transcript"] = placement_speaking_transcript.strip()

    if placement_speaking_score is not _UNSET:
        if (
            isinstance(placement_speaking_score, bool)
            or not isinstance(placement_speaking_score, (int, float))
            or not (0 <= placement_speaking_score <= 1)
        ):
            raise ValueError("placement_speaking_score must be a number 0–1")
        updates["placement_speaking_score"] = float(placement_speaking_score)

    if placement_complete is not _UNSET:
        updates["placement_complete"] = _coerce_bool(
            placement_complete, field="placement_complete"
        )

    if not updates:
        return current
    updated = replace(current, **updates)
    if updated.intake_step == INTAKE_STEP_COMPLETE:
        _require_intake_complete(updated)
    if updated.consent_complete:
        _require_consent_complete(updated)
    _require_placement_stage(updated)
    if updated.placement_complete:
        _require_placement_complete(updated)
        # Keep FLAG + stage enum aligned for RESUME / GATE (bare complete PATCH).
        if updated.placement_stage != PLACEMENT_STAGE_COMPLETE:
            updated = replace(updated, placement_stage=PLACEMENT_STAGE_COMPLETE)
    return store.update_learner(updated)
