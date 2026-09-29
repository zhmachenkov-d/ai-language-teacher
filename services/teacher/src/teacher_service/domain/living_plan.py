"""Living plan creation: path/curriculum validation, difficulty bands, WEEK_FILL.

Domain owns propose → auto-select → atomic persist (AD-6/7). Callers inject
`now` for WEEK_FILL (prod = real UTC; tests = fixture). Never invents times
when slots yield zero hits (`schedule_unusable`). Never fakes `plan_complete`
on LLM/schedule failure.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from teacher_service.domain.learner import (
    DEFAULT_L1,
    DEFAULT_TARGET_LANGUAGE,
    Learner,
    WeeklySlot,
)
from teacher_service.ports.llm import LlmGenerationError

if TYPE_CHECKING:
    from teacher_service.ports.config import ConfigPort
    from teacher_service.ports.llm import LlmPort
    from teacher_service.ports.persistence import PersistencePort

DIFFICULTY_BEGINNER = "beginner"
DIFFICULTY_ELEMENTARY = "elementary"
DIFFICULTY_INTERMEDIATE = "intermediate"
DIFFICULTY_UPPER_INTERMEDIATE = "upper_intermediate"

DIFFICULTY_BANDS: tuple[str, ...] = (
    DIFFICULTY_BEGINNER,
    DIFFICULTY_ELEMENTARY,
    DIFFICULTY_INTERMEDIATE,
    DIFFICULTY_UPPER_INTERMEDIATE,
)

_MIN_PATHS = 2
_MAX_PATHS = 3

# Secret name mirrored from the config adapter so domain does not import adapters.
_SECRET_LLM_API_KEY = "llm_api_key"


class LivingPlanError(Exception):
    """Domain failure with a stable wire `code` for 422/404/500 envelopes."""

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class PathOption:
    id: str
    title: str
    summary: str
    recommended: bool


@dataclass(frozen=True)
class Curriculum:
    goals: tuple[str, ...]
    focus: str
    upcoming_topics: tuple[str, ...]


@dataclass(frozen=True)
class LessonRecord:
    """Scheduled lesson projection — schedule fields only (2.4 LESSON_WIRE)."""

    id: str
    living_plan_id: str
    scheduled_at: datetime  # UTC aware
    timezone: str


@dataclass(frozen=True)
class LivingPlan:
    id: str
    learner_id: str
    goals: tuple[str, ...]
    focus: str
    upcoming_topics: tuple[str, ...]
    difficulty: str
    selected_path_id: str
    proposed_paths: tuple[PathOption, ...]
    revisable: bool
    target_language: str
    l1: str


@dataclass(frozen=True)
class LivingPlanProjection:
    """Wire-shaped living plan + WEEK_FILL lessons."""

    plan: LivingPlan
    lessons: tuple[LessonRecord, ...]


def seed_difficulty(*, listening_score: float | None, speaking_score: float | None) -> str:
    """Map avg(listening, speaking) onto CEFR-ish v1 bands.

    Bands: beginner [0,0.25) | elementary [0.25,0.5) | intermediate [0.5,0.75)
    | upper_intermediate [0.75,1]. Missing scores → `placement_scores_missing`.
    """
    if listening_score is None or speaking_score is None:
        raise LivingPlanError(
            "placement_scores_missing",
            "listening and speaking scores are required before plan creation",
        )
    for name, value in (
        ("listening_score", listening_score),
        ("speaking_score", speaking_score),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not (0 <= float(value) <= 1)
        ):
            raise LivingPlanError(
                "placement_scores_missing",
                f"{name} must be a number 0–1",
            )
    avg = (float(listening_score) + float(speaking_score)) / 2.0
    if avg < 0.25:
        return DIFFICULTY_BEGINNER
    if avg < 0.5:
        return DIFFICULTY_ELEMENTARY
    if avg < 0.75:
        return DIFFICULTY_INTERMEDIATE
    return DIFFICULTY_UPPER_INTERMEDIATE


def parse_path_options(raw: Any) -> tuple[PathOption, ...]:
    """Validate LLM path options: 2–3 items with `{id,title,summary,recommended}`."""
    if not isinstance(raw, list) or not (_MIN_PATHS <= len(raw) <= _MAX_PATHS):
        raise LivingPlanError(
            "llm_generation_failed",
            f"paths must contain {_MIN_PATHS}–{_MAX_PATHS} options",
            retryable=True,
        )
    paths: list[PathOption] = []
    seen_ids: set[str] = set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise LivingPlanError(
                "llm_generation_failed",
                f"paths[{i}] must be an object",
                retryable=True,
            )
        path_id = item.get("id")
        title = item.get("title")
        summary = item.get("summary")
        recommended = item.get("recommended")
        if not isinstance(path_id, str) or not path_id.strip():
            raise LivingPlanError(
                "llm_generation_failed",
                f"paths[{i}].id must be a non-empty string",
                retryable=True,
            )
        if not isinstance(title, str) or not title.strip():
            raise LivingPlanError(
                "llm_generation_failed",
                f"paths[{i}].title must be a non-empty string",
                retryable=True,
            )
        if not isinstance(summary, str) or not summary.strip():
            raise LivingPlanError(
                "llm_generation_failed",
                f"paths[{i}].summary must be a non-empty string",
                retryable=True,
            )
        if not isinstance(recommended, bool):
            raise LivingPlanError(
                "llm_generation_failed",
                f"paths[{i}].recommended must be a boolean",
                retryable=True,
            )
        cleaned_id = path_id.strip()
        if cleaned_id in seen_ids:
            raise LivingPlanError(
                "llm_generation_failed",
                f"paths[{i}].id is duplicated",
                retryable=True,
            )
        seen_ids.add(cleaned_id)
        paths.append(
            PathOption(
                id=cleaned_id,
                title=title.strip(),
                summary=summary.strip(),
                recommended=recommended,
            )
        )
    return tuple(paths)


def parse_curriculum(raw: Any) -> Curriculum:
    """Validate LLM curriculum: `goals`, `focus`, `upcoming_topics`."""
    if not isinstance(raw, dict):
        raise LivingPlanError(
            "llm_generation_failed",
            "curriculum payload must be an object",
            retryable=True,
        )
    goals_raw = raw.get("goals")
    focus = raw.get("focus")
    topics_raw = raw.get("upcoming_topics")
    if (
        not isinstance(goals_raw, list)
        or not goals_raw
        or not all(isinstance(g, str) and g.strip() for g in goals_raw)
    ):
        raise LivingPlanError(
            "llm_generation_failed",
            "goals must be a non-empty list of non-empty strings",
            retryable=True,
        )
    if not isinstance(focus, str) or not focus.strip():
        raise LivingPlanError(
            "llm_generation_failed",
            "focus must be a non-empty string",
            retryable=True,
        )
    if (
        not isinstance(topics_raw, list)
        or not topics_raw
        or not all(isinstance(t, str) and t.strip() for t in topics_raw)
    ):
        raise LivingPlanError(
            "llm_generation_failed",
            "upcoming_topics must be a non-empty list of non-empty strings",
            retryable=True,
        )
    return Curriculum(
        goals=tuple(g.strip() for g in goals_raw),
        focus=focus.strip(),
        upcoming_topics=tuple(t.strip() for t in topics_raw),
    )


def parse_propose_payload(raw: Any) -> tuple[tuple[PathOption, ...], Curriculum]:
    """Validate the combined LLM propose payload (paths + curriculum fields)."""
    if not isinstance(raw, dict):
        raise LivingPlanError(
            "llm_generation_failed",
            "LLM propose payload must be an object",
            retryable=True,
        )
    paths = parse_path_options(raw.get("paths"))
    curriculum = parse_curriculum(raw)
    return paths, curriculum


def select_path(paths: Sequence[PathOption]) -> PathOption:
    """Auto-select the recommended path; if not exactly one, force the first."""
    recommended = [p for p in paths if p.recommended]
    if len(recommended) == 1:
        return recommended[0]
    return paths[0]


def week_fill_occurrences(
    slots: Sequence[WeeklySlot],
    *,
    tz_name: str,
    now: datetime,
) -> list[datetime]:
    """Per slot: earliest local occurrence with `local_dt > now` in `[now, now+7d)`.

    Returns UTC-aware datetimes. Empty slots or zero hits → empty list (caller
    raises `schedule_unusable`). Does not invent times.
    """
    if not slots:
        return []
    if now.tzinfo is None:
        now_utc = now.replace(tzinfo=timezone.utc)
    else:
        now_utc = now.astimezone(timezone.utc)
    window_end = now_utc + timedelta(days=7)

    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        # Invalid IANA → no usable hits (DST/IANA hardening is deferred-work).
        return []

    local_now = now_utc.astimezone(tz)
    results: list[datetime] = []
    for slot in slots:
        hit: datetime | None = None
        for day_offset in range(0, 8):
            day = local_now.date() + timedelta(days=day_offset)
            if day.weekday() != slot.weekday:
                continue
            local_dt = datetime(
                day.year,
                day.month,
                day.day,
                slot.start_minute // 60,
                slot.start_minute % 60,
                tzinfo=tz,
            )
            utc_dt = local_dt.astimezone(timezone.utc)
            # local_dt > now ∧ utc_dt ∈ [now, now+7d)  → effectively (now, now+7d)
            if utc_dt > now_utc and utc_dt < window_end:
                hit = utc_dt
                break
        if hit is not None:
            results.append(hit)
    return results


def living_plan_to_wire(projection: LivingPlanProjection) -> dict[str, Any]:
    """Snake_case LivingPlan projection including LESSON_WIRE lessons."""
    plan = projection.plan
    return {
        "id": plan.id,
        "goals": list(plan.goals),
        "focus": plan.focus,
        "upcoming_topics": list(plan.upcoming_topics),
        "difficulty": plan.difficulty,
        "selected_path_id": plan.selected_path_id,
        "proposed_paths": [
            {
                "id": p.id,
                "title": p.title,
                "summary": p.summary,
                "recommended": p.recommended,
            }
            for p in plan.proposed_paths
        ],
        "revisable": plan.revisable,
        "target_language": plan.target_language,
        "l1": plan.l1,
        "lessons": [
            {
                "id": lesson.id,
                "scheduled_at": lesson.scheduled_at.astimezone(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "timezone": lesson.timezone,
            }
            for lesson in projection.lessons
        ],
    }


def _load_living_plan_or_inconsistent(
    store: PersistencePort, learner_id: str
) -> LivingPlanProjection | None:
    """Load plan; map corrupt row data to `plan_inconsistent`."""
    try:
        return store.load_living_plan(learner_id)
    except ValueError as exc:
        raise LivingPlanError(
            "plan_inconsistent",
            str(exc),
        ) from exc


def _ensure_plan_complete_flag(
    store: PersistencePort, learner: Learner
) -> None:
    """Heal `plan_complete` when a LivingPlan row already exists without the FLAG."""
    if learner.plan_complete:
        return
    from dataclasses import replace

    try:
        store.update_learner(replace(learner, plan_complete=True))
    except Exception as exc:
        raise LivingPlanError(
            "plan_inconsistent",
            f"living plan exists but plan_complete could not be healed: {exc}",
        ) from exc


def get_living_plan(store: PersistencePort, learner: Learner) -> LivingPlanProjection:
    """Load the LivingPlan for GET /living-plan — FLAG-gated.

    !FLAG → 404 `living_plan_not_found`; FLAG without row → 500 `plan_inconsistent`.
    """
    if not learner.plan_complete:
        raise LivingPlanError(
            "living_plan_not_found",
            "living plan has not been created yet",
        )
    loaded = _load_living_plan_or_inconsistent(store, learner.id)
    if loaded is None:
        raise LivingPlanError(
            "plan_inconsistent",
            "plan_complete is set but no living plan row exists",
        )
    return loaded


def create_living_plan(
    store: PersistencePort,
    llm: LlmPort,
    config: ConfigPort,
    *,
    now: datetime | None = None,
    llm_configured: Callable[[ConfigPort], bool] | None = None,
) -> LivingPlanProjection:
    """Propose paths via LLM, auto-select, WEEK_FILL, atomically persist + FLAG.

    Idempotent when a LivingPlan already exists for the learner (no re-LLM).
    """
    from teacher_service.domain.learner import get_or_create_learner

    learner = get_or_create_learner(store)

    existing = _load_living_plan_or_inconsistent(store, learner.id)
    if existing is not None:
        _ensure_plan_complete_flag(store, learner)
        return existing

    if not learner.placement_complete:
        raise LivingPlanError(
            "placement_incomplete",
            "placement_complete is required before plan creation",
        )

    difficulty = seed_difficulty(
        listening_score=learner.placement_listening_score,
        speaking_score=learner.placement_speaking_score,
    )

    if now is None:
        now = datetime.now(timezone.utc)

    occurrences = week_fill_occurrences(
        learner.weekly_slots,
        tz_name=learner.timezone,
        now=now,
    )
    if not occurrences:
        raise LivingPlanError(
            "schedule_unusable",
            "no usable lesson times in the next 7 days from weekly_slots",
        )

    def _default_llm_configured(cfg: ConfigPort) -> bool:
        try:
            return cfg.get_secret(_SECRET_LLM_API_KEY) is not None
        except RuntimeError as exc:
            raise LivingPlanError(
                "llm_config_missing",
                str(exc),
                retryable=True,
            ) from exc

    check_configured = llm_configured or _default_llm_configured
    if not check_configured(config):
        raise LivingPlanError(
            "llm_config_missing",
            "LLM API key is not configured",
            retryable=True,
        )

    try:
        raw = llm.propose_learning_paths(
            target_language=learner.target_language,
            l1=learner.l1,
            goals=learner.goals,
            desired_outcome=learner.desired_outcome,
            interests=learner.interests,
            emphasis=learner.emphasis,
            difficulty=difficulty,
        )
    except LlmGenerationError as exc:
        raise LivingPlanError(
            "llm_generation_failed",
            str(exc),
            retryable=True,
        ) from exc
    except Exception as exc:
        raise LivingPlanError(
            "llm_generation_failed",
            str(exc),
            retryable=True,
        ) from exc

    try:
        paths, curriculum = parse_propose_payload(raw)
    except LivingPlanError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise LivingPlanError(
            "llm_generation_failed",
            str(exc),
            retryable=True,
        ) from exc

    selected = select_path(paths)
    plan_id = str(uuid.uuid4())
    plan = LivingPlan(
        id=plan_id,
        learner_id=learner.id,
        goals=curriculum.goals,
        focus=curriculum.focus,
        upcoming_topics=curriculum.upcoming_topics,
        difficulty=difficulty,
        selected_path_id=selected.id,
        proposed_paths=paths,
        revisable=True,
        target_language=learner.target_language or DEFAULT_TARGET_LANGUAGE,
        l1=learner.l1 or DEFAULT_L1,
    )
    lessons = tuple(
        LessonRecord(
            id=str(uuid.uuid4()),
            living_plan_id=plan_id,
            scheduled_at=occ if occ.tzinfo else occ.replace(tzinfo=timezone.utc),
            timezone=learner.timezone,
        )
        for occ in occurrences
    )

    try:
        return store.create_living_plan_atomic(plan, lessons)
    except Exception as exc:
        # UNIQUE(learner_id) race → treat as idempotent success.
        raced = _load_living_plan_or_inconsistent(store, learner.id)
        if raced is not None:
            # Re-load learner in case FLAG was set by the winning txn.
            fresh = get_or_create_learner(store)
            _ensure_plan_complete_flag(store, fresh)
            return raced
        raise LivingPlanError(
            "llm_generation_failed",
            f"failed to persist living plan: {exc}",
            retryable=True,
        ) from exc
