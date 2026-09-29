"""UNIQUE(learner_id) race → create_living_plan reload idempotent path.

API suites cover happy-path idempotent POST and raw UNIQUE IntegrityError on
SQLite; this exercises the domain `except`/`load` branch the concurrent loser hits.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from teacher_service.adapters.config import SECRET_LLM_API_KEY, FileConfig
from teacher_service.adapters.persistence import SqliteStore
from teacher_service.domain.learner import (
    INTAKE_STEP_COMPLETE,
    Learner,
    WeeklySlot,
)
from teacher_service.domain.living_plan import (
    DIFFICULTY_INTERMEDIATE,
    LessonRecord,
    LivingPlan,
    LivingPlanError,
    LivingPlanProjection,
    PathOption,
    create_living_plan,
)
from teacher_service.domain.placement import PLACEMENT_STAGE_COMPLETE


class FakeLlmPort:
    def __init__(self, propose: dict[str, Any]) -> None:
        self.propose = propose
        self.propose_calls = 0

    def generate_placement_items(self, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("placement LLM unused")

    def propose_learning_paths(self, **_kwargs: Any) -> dict[str, Any]:
        self.propose_calls += 1
        return self.propose


class RaceStore:
    """First load empty; create raises UNIQUE; subsequent load returns winner."""

    def __init__(self, inner: SqliteStore, winner: LivingPlanProjection) -> None:
        self._inner = inner
        self._winner = winner
        self.create_calls = 0

    def create_learner(self, learner: Learner) -> Learner:
        return self._inner.create_learner(learner)

    def load_learner(self) -> Learner | None:
        return self._inner.load_learner()

    def update_learner(self, learner: Learner) -> Learner:
        return self._inner.update_learner(learner)

    def load_living_plan(self, learner_id: str) -> LivingPlanProjection | None:
        if self.create_calls == 0:
            return None
        return self._winner

    def create_living_plan_atomic(
        self,
        plan: LivingPlan,
        lessons: tuple[LessonRecord, ...],
    ) -> LivingPlanProjection:
        self.create_calls += 1
        raise sqlite3.IntegrityError(
            "UNIQUE constraint failed: living_plan.learner_id"
        )


class EmptyAfterRaceStore(RaceStore):
    """IntegrityError but reload still empty → must not fabricate success."""

    def load_living_plan(self, learner_id: str) -> LivingPlanProjection | None:
        return None


@pytest.fixture
def config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FileConfig:
    root = tmp_path / "teacher-data"
    monkeypatch.setenv("TEACHER_DATA_DIR", str(root))
    cfg = FileConfig(root)
    cfg.ensure_layout()
    cfg.set_secret(SECRET_LLM_API_KEY, "sk-test")
    return cfg


def _seed_placement_ready(store: SqliteStore) -> Learner:
    learner = Learner(
        id="learner-race-1",
        target_language="en",
        l1="ru",
        timezone="Europe/Moscow",
        goals=("Учёба",),
        desired_outcome=("Разговор",),
        interests=("Технологии",),
        emphasis=("Говорение",),
        weekly_slots=(WeeklySlot(weekday=0, start_minute=600),),
        intake_step=INTAKE_STEP_COMPLETE,
        consent_complete=True,
        placement_stage=PLACEMENT_STAGE_COMPLETE,
        placement_listening_score=0.6,
        placement_speaking_score=0.7,
        placement_speaking_transcript="enough words for speaking",
        placement_complete=True,
        plan_complete=False,
    )
    return store.create_learner(learner)


def _propose_payload() -> dict[str, Any]:
    return {
        "paths": [
            {
                "id": "conv",
                "title": "Conversation",
                "summary": "Speak early",
                "recommended": True,
            },
            {
                "id": "grammar",
                "title": "Grammar",
                "summary": "Structure first",
                "recommended": False,
            },
        ],
        "goals": ["Hold a chat"],
        "focus": "Speaking",
        "upcoming_topics": ["Greetings"],
    }


def _winner_projection(learner_id: str) -> LivingPlanProjection:
    plan_id = "winner-plan-id"
    return LivingPlanProjection(
        plan=LivingPlan(
            id=plan_id,
            learner_id=learner_id,
            goals=("Hold a chat",),
            focus="Speaking",
            upcoming_topics=("Greetings",),
            difficulty=DIFFICULTY_INTERMEDIATE,
            selected_path_id="conv",
            proposed_paths=(
                PathOption("conv", "Conversation", "Speak early", True),
                PathOption("grammar", "Grammar", "Structure first", False),
            ),
            revisable=True,
            target_language="en",
            l1="ru",
        ),
        lessons=(
            LessonRecord(
                id="lesson-1",
                living_plan_id=plan_id,
                scheduled_at=datetime(2026, 3, 2, 7, 0, tzinfo=timezone.utc),
                timezone="Europe/Moscow",
            ),
        ),
    )


def test_unique_race_reloads_winner_idempotently(config: FileConfig) -> None:
    store = SqliteStore(config.sqlite_path())
    learner = _seed_placement_ready(store)
    winner = _winner_projection(learner.id)
    race = RaceStore(store, winner)
    llm = FakeLlmPort(_propose_payload())
    now = datetime(2026, 3, 2, 6, 0, tzinfo=timezone.utc)

    result = create_living_plan(race, llm, config, now=now)

    assert race.create_calls == 1
    assert llm.propose_calls == 1
    assert result.plan.id == "winner-plan-id"
    assert result is winner
    # Loser must heal plan_complete on the underlying learner row.
    refreshed = store.load_learner()
    assert refreshed is not None
    assert refreshed.plan_complete is True


def test_unique_race_without_winner_row_raises(config: FileConfig) -> None:
    store = SqliteStore(config.sqlite_path())
    _seed_placement_ready(store)
    race = EmptyAfterRaceStore(store, _winner_projection("unused"))
    llm = FakeLlmPort(_propose_payload())
    now = datetime(2026, 3, 2, 6, 0, tzinfo=timezone.utc)

    with pytest.raises(LivingPlanError) as exc:
        create_living_plan(race, llm, config, now=now)

    assert exc.value.code == "llm_generation_failed"
    assert exc.value.retryable is True
    assert race.create_calls == 1
    assert llm.propose_calls == 1
