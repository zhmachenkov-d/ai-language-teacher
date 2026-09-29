"""WEEK_FILL is recomputed after LLM so slow proposes cannot persist past times."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from teacher_service.adapters.config import SECRET_LLM_API_KEY, FileConfig
from teacher_service.adapters.persistence import SqliteStore
from teacher_service.domain.learner import (
    INTAKE_STEP_COMPLETE,
    Learner,
    WeeklySlot,
)
from teacher_service.domain.living_plan import create_living_plan
from teacher_service.domain.placement import PLACEMENT_STAGE_COMPLETE


class AdvancingClockLlm:
    """Advances the shared clock across a slot boundary during propose."""

    def __init__(
        self,
        propose: dict[str, Any],
        clock: list[datetime],
        after_propose: datetime,
    ) -> None:
        self.propose = propose
        self._clock = clock
        self._after_propose = after_propose
        self.propose_calls = 0

    def generate_placement_items(self, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("placement LLM unused")

    def propose_learning_paths(self, **_kwargs: Any) -> dict[str, Any]:
        self.propose_calls += 1
        self._clock[0] = self._after_propose
        return self.propose


@pytest.fixture
def config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FileConfig:
    root = tmp_path / "teacher-data"
    monkeypatch.setenv("TEACHER_DATA_DIR", str(root))
    cfg = FileConfig(root)
    cfg.ensure_layout()
    cfg.set_secret(SECRET_LLM_API_KEY, "sk-test")
    return cfg


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


def test_week_fill_recomputed_after_slow_llm(config: FileConfig) -> None:
    # Monday 10:00 MSK (= 07:00 UTC). Pre-LLM now is before the slot; during
    # propose the clock crosses the boundary so persist must use next week.
    store = SqliteStore(config.sqlite_path())
    store.create_learner(
        Learner(
            id="learner-week-fill-1",
            target_language="en",
            l1="ru",
            timezone="Europe/Moscow",
            goals=("Учёба",),
            desired_outcome=("Разговор",),
            interests=("Технологии",),
            emphasis=("Говорение",),
            weekly_slots=(WeeklySlot(weekday=0, start_minute=10 * 60),),
            intake_step=INTAKE_STEP_COMPLETE,
            consent_complete=True,
            placement_stage=PLACEMENT_STAGE_COMPLETE,
            placement_listening_score=0.6,
            placement_speaking_score=0.7,
            placement_speaking_transcript="enough words for speaking",
            placement_complete=True,
            plan_complete=False,
        )
    )

    before = datetime(2026, 3, 2, 6, 50, tzinfo=timezone.utc)  # Mon 09:50 MSK
    after = datetime(2026, 3, 2, 7, 5, tzinfo=timezone.utc)  # Mon 10:05 MSK
    clock = [before]
    llm = AdvancingClockLlm(_propose_payload(), clock, after)

    result = create_living_plan(
        store,
        llm,
        config,
        now_provider=lambda: clock[0],
    )

    assert llm.propose_calls == 1
    assert len(result.lessons) == 1
    local = result.lessons[0].scheduled_at.astimezone(ZoneInfo("Europe/Moscow"))
    assert local.date().isoformat() == "2026-03-09"
    assert local.hour == 10
    assert local.minute == 0
    # Must not have persisted the same-day slot that was already past after LLM.
    assert result.lessons[0].scheduled_at != datetime(
        2026, 3, 2, 7, 0, tzinfo=timezone.utc
    )
