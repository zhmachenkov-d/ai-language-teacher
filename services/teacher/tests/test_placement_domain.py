"""Pure domain tests: placement item parsing/scoring + Learner update-learner gating."""

from __future__ import annotations

from pathlib import Path

import pytest
from teacher_service.adapters.config import FileConfig
from teacher_service.adapters.persistence import SqliteStore
from teacher_service.domain.learner import (
    INTAKE_STEP_COMPLETE,
    LearnerValidationError,
    WeeklySlot,
    update_learner,
)
from teacher_service.domain.placement import (
    ChoiceItem,
    ListeningContent,
    PlacementItems,
    PlacementItemsError,
    parse_placement_items,
    placement_items_public,
    placement_items_to_storage,
    score_choice_answers,
    score_speaking_transcript,
)


def _valid_raw_items() -> dict:
    return {
        "written": [
            {"prompt": f"Q{i}", "options": ["a", "b", "c"], "correct_index": 0}
            for i in range(5)
        ],
        "listening": {
            "script": "A short passage about daily life.",
            "questions": [
                {"prompt": f"L{i}", "options": ["a", "b", "c"], "correct_index": 1}
                for i in range(3)
            ],
        },
        "speaking_prompts": ["Tell me about your day.", "Describe your job.", "Plans?"],
    }


class TestParsePlacementItems:
    def test_valid_payload_round_trips(self) -> None:
        items = parse_placement_items(_valid_raw_items())
        assert len(items.written) == 5
        assert len(items.listening.questions) == 3
        assert len(items.speaking_prompts) == 3

    def test_storage_dict_includes_correct_index(self) -> None:
        items = parse_placement_items(_valid_raw_items())
        stored = placement_items_to_storage(items)
        assert stored["written"][0]["correct_index"] == 0
        # Round-trips back through parse.
        assert parse_placement_items(stored).written[0].correct_index == 0

    def test_public_dict_strips_correct_index_and_script(self) -> None:
        items = parse_placement_items(_valid_raw_items())
        public = placement_items_public(items)
        assert "correct_index" not in public["written"][0]
        assert "script" not in public["listening"]
        assert "correct_index" not in public["listening"]["questions"][0]
        # Defense-in-depth: even if a nested answer-key sneaks into a
        # hand-built payload, scrub drops it before the wire.
        sneaky = placement_items_public(items)
        sneaky["written"][0]["correct_index"] = 0
        sneaky["listening"]["script"] = "secret"
        from teacher_service.domain.placement import _scrub_answer_keys

        scrubbed = _scrub_answer_keys(sneaky)
        assert "correct_index" not in scrubbed["written"][0]
        assert "script" not in scrubbed["listening"]
        assert public["speaking_prompts"] == [
            "Tell me about your day.",
            "Describe your job.",
            "Plans?",
        ]

    @pytest.mark.parametrize(
        "mutate",
        [
            lambda raw: raw.pop("written"),
            lambda raw: raw["written"].pop(),  # wrong count
            lambda raw: raw["written"][0].__setitem__("options", ["only-one"]),
            lambda raw: raw["written"][0].__setitem__("correct_index", 99),
            lambda raw: raw["listening"].pop("script"),
            lambda raw: raw["listening"]["questions"].pop(),
            lambda raw: raw.pop("speaking_prompts"),
            lambda raw: raw.__setitem__("speaking_prompts", ["only one"]),
        ],
    )
    def test_malformed_payload_raises(self, mutate) -> None:
        raw = _valid_raw_items()
        mutate(raw)
        with pytest.raises(PlacementItemsError):
            parse_placement_items(raw)

    def test_non_dict_payload_raises(self) -> None:
        with pytest.raises(PlacementItemsError):
            parse_placement_items(["not", "a", "dict"])


class TestScoring:
    def test_score_choice_answers_all_correct(self) -> None:
        items = (
            ChoiceItem(prompt="p", options=("a", "b"), correct_index=0),
            ChoiceItem(prompt="p2", options=("a", "b"), correct_index=1),
        )
        assert score_choice_answers(items, [0, 1]) == 1.0

    def test_score_choice_answers_partial(self) -> None:
        items = (
            ChoiceItem(prompt="p", options=("a", "b"), correct_index=0),
            ChoiceItem(prompt="p2", options=("a", "b"), correct_index=1),
        )
        assert score_choice_answers(items, [0, 0]) == 0.5

    def test_score_choice_answers_length_mismatch_raises(self) -> None:
        items = (ChoiceItem(prompt="p", options=("a", "b"), correct_index=0),)
        with pytest.raises(ValueError):
            score_choice_answers(items, [0, 1])

    def test_score_speaking_transcript_rewards_length(self) -> None:
        prompts = ["a", "b", "c"]  # target = 45 words
        short = score_speaking_transcript("one two three", prompts)
        long_transcript = " ".join(["word"] * 45)
        full = score_speaking_transcript(long_transcript, prompts)
        assert 0.0 < short < full
        assert full == 1.0

    def test_score_speaking_transcript_caps_at_one(self) -> None:
        prompts = ["a"]
        huge = " ".join(["word"] * 1000)
        assert score_speaking_transcript(huge, prompts) == 1.0


@pytest.fixture
def store(tmp_path: Path) -> SqliteStore:
    config = FileConfig(tmp_path / "data")
    config.ensure_layout()
    return SqliteStore(config.sqlite_path())


def _consented_learner(store: SqliteStore):
    return update_learner(
        store,
        address_as="Саша",
        age=30,
        goals=["Учёба"],
        desired_outcome=["Уверенный разговор"],
        interests=["Технологии"],
        emphasis=["Говорение"],
        lesson_duration_minutes=45,
        timezone="Europe/Moscow",
        weekly_slots=[WeeklySlot(weekday=0, start_minute=540)],
        intake_step=INTAKE_STEP_COMPLETE,
    )


class TestPlacementGating:
    def test_placement_field_requires_consent(self, store: SqliteStore) -> None:
        with pytest.raises(LearnerValidationError) as exc_info:
            update_learner(store, placement_stage="written")
        assert exc_info.value.code == "placement_requires_consent"

    def test_written_answers_require_items_first(self, store: SqliteStore) -> None:
        with pytest.raises(ValueError):
            update_learner(store, placement_written_answers=[0, 0, 0, 0, 0])

    def test_full_happy_path_reaches_complete(self, store: SqliteStore) -> None:
        from teacher_service.domain.learner import update_learner as _update

        _consented_learner(store)
        _update(
            store,
            consent_mic=True,
            consent_ai=True,
            consent_privacy=True,
            consent_complete=True,
        )
        items = parse_placement_items(_valid_raw_items())
        stored_items = placement_items_to_storage(items)
        _update(store, placement_items=stored_items, placement_stage="written")
        learner = _update(
            store,
            placement_written_answers=[0, 0, 0, 0, 0],
            placement_stage="listening",
        )
        assert learner.placement_written_score == 1.0

        learner = _update(store, placement_listening_generated=True)
        learner = _update(
            store,
            placement_listening_played=True,
            placement_listening_answers=[1, 1, 1],
            placement_stage="speaking",
        )
        assert learner.placement_listening_score == 1.0

        learner = _update(
            store,
            placement_speaking_transcript="a real transcript with enough words " * 5,
            placement_speaking_score=0.8,
            placement_stage="complete",
            placement_complete=True,
        )
        assert learner.placement_complete is True
        assert learner.placement_stage == "complete"

    def test_placement_complete_rejected_without_speaking(
        self, store: SqliteStore
    ) -> None:
        from teacher_service.domain.learner import update_learner as _update

        _consented_learner(store)
        _update(
            store,
            consent_mic=True,
            consent_ai=True,
            consent_privacy=True,
            consent_complete=True,
        )
        items = parse_placement_items(_valid_raw_items())
        _update(store, placement_items=placement_items_to_storage(items))
        _update(store, placement_written_answers=[0, 0, 0, 0, 0])
        _update(store, placement_listening_generated=True)
        _update(store, placement_listening_played=True, placement_listening_answers=[1, 1, 1])

        with pytest.raises(LearnerValidationError) as exc_info:
            _update(store, placement_complete=True)
        assert exc_info.value.code == "placement_speaking_incomplete"

    def test_placement_complete_rejected_without_speaking_score(
        self, store: SqliteStore
    ) -> None:
        """Transcript alone is not seedable — score must be server-computed too."""
        from teacher_service.domain.learner import update_learner as _update

        _consented_learner(store)
        _update(
            store,
            consent_mic=True,
            consent_ai=True,
            consent_privacy=True,
            consent_complete=True,
        )
        items = parse_placement_items(_valid_raw_items())
        _update(store, placement_items=placement_items_to_storage(items))
        _update(store, placement_written_answers=[0, 0, 0, 0, 0])
        _update(store, placement_listening_generated=True)
        _update(store, placement_listening_played=True, placement_listening_answers=[1, 1, 1])
        _update(store, placement_speaking_transcript="hello world " * 10)

        with pytest.raises(LearnerValidationError) as exc_info:
            _update(store, placement_complete=True)
        assert exc_info.value.code == "placement_speaking_incomplete"

    def test_placement_complete_coerces_stage_to_complete(
        self, store: SqliteStore
    ) -> None:
        """Bare complete FLAG keeps stage enum aligned for RESUME."""
        from teacher_service.domain.learner import update_learner as _update

        _consented_learner(store)
        _update(
            store,
            consent_mic=True,
            consent_ai=True,
            consent_privacy=True,
            consent_complete=True,
        )
        items = parse_placement_items(_valid_raw_items())
        _update(store, placement_items=placement_items_to_storage(items))
        _update(store, placement_written_answers=[0, 0, 0, 0, 0])
        _update(store, placement_listening_generated=True)
        _update(store, placement_listening_played=True, placement_listening_answers=[1, 1, 1])
        _update(
            store,
            placement_speaking_transcript="hello world " * 10,
            placement_speaking_score=0.5,
            placement_stage="speaking",
        )

        learner = _update(store, placement_complete=True)
        assert learner.placement_complete is True
        assert learner.placement_stage == "complete"

    def test_placement_complete_rejected_without_listening(
        self, store: SqliteStore
    ) -> None:
        from teacher_service.domain.learner import update_learner as _update

        _consented_learner(store)
        _update(
            store,
            consent_mic=True,
            consent_ai=True,
            consent_privacy=True,
            consent_complete=True,
        )
        items = parse_placement_items(_valid_raw_items())
        _update(store, placement_items=placement_items_to_storage(items))
        _update(store, placement_written_answers=[0, 0, 0, 0, 0])

        with pytest.raises(LearnerValidationError) as exc_info:
            _update(
                store,
                placement_speaking_transcript="hello world " * 10,
                placement_complete=True,
            )
        assert exc_info.value.code == "placement_listening_incomplete"

    def test_listening_stage_requires_generated_flag_not_just_played(
        self, store: SqliteStore
    ) -> None:
        """Client cannot fake `played` without the server ever synthesizing audio."""
        from teacher_service.domain.learner import update_learner as _update

        _consented_learner(store)
        _update(
            store,
            consent_mic=True,
            consent_ai=True,
            consent_privacy=True,
            consent_complete=True,
        )
        items = parse_placement_items(_valid_raw_items())
        _update(store, placement_items=placement_items_to_storage(items))
        _update(store, placement_written_answers=[0, 0, 0, 0, 0])

        with pytest.raises(LearnerValidationError) as exc_info:
            _update(
                store,
                placement_listening_played=True,
                placement_listening_answers=[1, 1, 1],
                placement_stage="speaking",
            )
        assert exc_info.value.code == "placement_listening_incomplete"
