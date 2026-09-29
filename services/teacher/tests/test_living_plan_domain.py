"""Pure domain tests: difficulty bands, path/curriculum parse, WEEK_FILL, select."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from teacher_service.domain.learner import WeeklySlot
from teacher_service.domain.living_plan import (
    DIFFICULTY_BEGINNER,
    DIFFICULTY_ELEMENTARY,
    DIFFICULTY_INTERMEDIATE,
    DIFFICULTY_UPPER_INTERMEDIATE,
    LivingPlanError,
    PathOption,
    parse_path_options,
    parse_propose_payload,
    seed_difficulty,
    select_path,
    week_fill_occurrences,
)


class TestSeedDifficulty:
    @pytest.mark.parametrize(
        ("listening", "speaking", "expected"),
        [
            (0.0, 0.0, DIFFICULTY_BEGINNER),
            (0.2, 0.2, DIFFICULTY_BEGINNER),
            (0.24, 0.24, DIFFICULTY_BEGINNER),
            (0.25, 0.25, DIFFICULTY_ELEMENTARY),
            (0.4, 0.4, DIFFICULTY_ELEMENTARY),
            (0.5, 0.5, DIFFICULTY_INTERMEDIATE),
            (0.7, 0.7, DIFFICULTY_INTERMEDIATE),
            (0.75, 0.75, DIFFICULTY_UPPER_INTERMEDIATE),
            (1.0, 1.0, DIFFICULTY_UPPER_INTERMEDIATE),
            (0.9, 0.1, DIFFICULTY_INTERMEDIATE),  # avg 0.5
        ],
    )
    def test_bands(
        self, listening: float, speaking: float, expected: str
    ) -> None:
        assert (
            seed_difficulty(listening_score=listening, speaking_score=speaking)
            == expected
        )

    def test_missing_scores_raise(self) -> None:
        with pytest.raises(LivingPlanError) as exc:
            seed_difficulty(listening_score=None, speaking_score=0.5)
        assert exc.value.code == "placement_scores_missing"
        with pytest.raises(LivingPlanError) as exc2:
            seed_difficulty(listening_score=0.5, speaking_score=None)
        assert exc2.value.code == "placement_scores_missing"


class TestParsePathsAndCurriculum:
    def test_valid_propose_payload(self) -> None:
        paths, curriculum = parse_propose_payload(
            {
                "paths": [
                    {
                        "id": "a",
                        "title": "Path A",
                        "summary": "Summary A",
                        "recommended": False,
                    },
                    {
                        "id": "b",
                        "title": "Path B",
                        "summary": "Summary B",
                        "recommended": True,
                    },
                ],
                "goals": ["Speak fluently"],
                "focus": "Conversation",
                "upcoming_topics": ["Greetings", "Work"],
            }
        )
        assert len(paths) == 2
        assert curriculum.focus == "Conversation"
        assert select_path(paths).id == "b"

    def test_invalid_path_count(self) -> None:
        with pytest.raises(LivingPlanError) as exc:
            parse_path_options(
                [{"id": "a", "title": "A", "summary": "S", "recommended": True}]
            )
        assert exc.value.code == "llm_generation_failed"

    def test_select_forces_first_when_not_exactly_one_recommended(self) -> None:
        paths = (
            PathOption(id="a", title="A", summary="S", recommended=False),
            PathOption(id="b", title="B", summary="S", recommended=False),
        )
        assert select_path(paths).id == "a"
        both = (
            PathOption(id="a", title="A", summary="S", recommended=True),
            PathOption(id="b", title="B", summary="S", recommended=True),
        )
        assert select_path(both).id == "a"


class TestWeekFill:
    def test_one_slot_next_occurrence(self) -> None:
        # Monday 09:00 Europe/Moscow; fixture now = Monday 2026-03-02 05:00 UTC
        # Moscow is UTC+3 → local Monday 08:00; slot Mon 09:00 is still ahead same day.
        now = datetime(2026, 3, 2, 5, 0, tzinfo=timezone.utc)
        slots = (WeeklySlot(weekday=0, start_minute=9 * 60),)
        hits = week_fill_occurrences(slots, tz_name="Europe/Moscow", now=now)
        assert len(hits) == 1
        local = hits[0].astimezone(ZoneInfo("Europe/Moscow"))
        assert local.weekday() == 0
        assert local.hour == 9
        assert local.minute == 0

    def test_slot_already_past_today_uses_next_week_if_in_window(self) -> None:
        # Monday 10:00 Moscow; slot Monday 09:00 → next Monday (within 7d).
        now = datetime(2026, 3, 2, 7, 0, tzinfo=timezone.utc)  # Mon 10:00 MSK
        slots = (WeeklySlot(weekday=0, start_minute=9 * 60),)
        hits = week_fill_occurrences(slots, tz_name="Europe/Moscow", now=now)
        assert len(hits) == 1
        local = hits[0].astimezone(ZoneInfo("Europe/Moscow"))
        assert local.date().isoformat() == "2026-03-09"

    def test_slot_at_exact_now_excludes_current_and_window_end(self) -> None:
        # now == this week's slot → omitted; next week == now+7d → excluded by [now, now+7d)
        now = datetime(2026, 3, 2, 6, 0, tzinfo=timezone.utc)  # Mon 09:00 MSK
        slots = (WeeklySlot(weekday=0, start_minute=9 * 60),)
        assert week_fill_occurrences(slots, tz_name="Europe/Moscow", now=now) == []

    def test_empty_slots_zero_hits(self) -> None:
        now = datetime(2026, 3, 2, 6, 0, tzinfo=timezone.utc)
        assert week_fill_occurrences((), tz_name="Europe/Moscow", now=now) == []

    def test_multiple_slots(self) -> None:
        now = datetime(2026, 3, 2, 6, 0, tzinfo=timezone.utc)  # Mon 09:00 MSK
        slots = (
            WeeklySlot(weekday=0, start_minute=10 * 60),  # Mon 10:00
            WeeklySlot(weekday=2, start_minute=18 * 60),  # Wed 18:00
        )
        hits = week_fill_occurrences(slots, tz_name="Europe/Moscow", now=now)
        assert len(hits) == 2
        assert hits[0] < hits[1]
