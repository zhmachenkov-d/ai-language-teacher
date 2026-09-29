"""Placement domain types: stages, LLM-generated items, and scoring.

Pure (no PersistencePort/LlmPort/VoicePort I/O). `teacher_service.domain.learner`
imports the parsing/scoring helpers here to validate and score PATCH /learner
placement fields; `adapters.api.app` imports the stage constants + item
(de)serialization helpers for the placement-specific endpoints.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

PLACEMENT_STAGE_BRIEFING = "briefing"
PLACEMENT_STAGE_WRITTEN = "written"
PLACEMENT_STAGE_LISTENING = "listening"
PLACEMENT_STAGE_SPEAKING = "speaking"
PLACEMENT_STAGE_COMPLETE = "complete"

PLACEMENT_STAGES: tuple[str, ...] = (
    PLACEMENT_STAGE_BRIEFING,
    PLACEMENT_STAGE_WRITTEN,
    PLACEMENT_STAGE_LISTENING,
    PLACEMENT_STAGE_SPEAKING,
    PLACEMENT_STAGE_COMPLETE,
)

# One LLM-generated item set per placement run — fixed shape so the API/UI
# never has to branch on a variable item count.
WRITTEN_ITEM_COUNT = 5
LISTENING_QUESTION_COUNT = 3
SPEAKING_PROMPT_COUNT = 3
_MIN_OPTIONS = 3
_MAX_OPTIONS = 5

# MVP speaking heuristic: transcript length vs. expected turns. This is a
# presence/aggregate check, not pronunciation/intonation scoring (Epic 3.7).
_SPEAKING_WORDS_PER_PROMPT = 15


class PlacementItemsError(ValueError):
    """LLM-generated placement items failed structural validation.

    Raised instead of falling back to fabricated items — CONTENT: LLM_GEN
    requires a clear retryable error, never a silent fake item set.
    """

    code = "llm_invalid_items"


@dataclass(frozen=True)
class ChoiceItem:
    """One multiple-choice item. `correct_index` is server-only (never sent to the client)."""

    prompt: str
    options: tuple[str, ...]
    correct_index: int


@dataclass(frozen=True)
class ListeningContent:
    script: str
    questions: tuple[ChoiceItem, ...]


@dataclass(frozen=True)
class PlacementItems:
    written: tuple[ChoiceItem, ...]
    listening: ListeningContent
    speaking_prompts: tuple[str, ...]


def _parse_choice_item(raw: Any, *, context: str) -> ChoiceItem:
    if not isinstance(raw, dict):
        raise PlacementItemsError(f"{context} must be an object")
    prompt = raw.get("prompt")
    options = raw.get("options")
    correct_index = raw.get("correct_index")
    if not isinstance(prompt, str) or not prompt.strip():
        raise PlacementItemsError(f"{context}.prompt must be a non-empty string")
    if (
        not isinstance(options, list)
        or not (_MIN_OPTIONS <= len(options) <= _MAX_OPTIONS)
        or not all(isinstance(o, str) and o.strip() for o in options)
    ):
        raise PlacementItemsError(
            f"{context}.options must be {_MIN_OPTIONS}-{_MAX_OPTIONS} non-empty strings"
        )
    if (
        isinstance(correct_index, bool)
        or not isinstance(correct_index, int)
        or not (0 <= correct_index < len(options))
    ):
        raise PlacementItemsError(
            f"{context}.correct_index must be a valid option index"
        )
    return ChoiceItem(
        prompt=prompt.strip(),
        options=tuple(o.strip() for o in options),
        correct_index=correct_index,
    )


def parse_placement_items(raw: Any) -> PlacementItems:
    """Validate an LLM-generated (or persisted) item payload.

    Raises `PlacementItemsError` on any structural mismatch — callers must
    surface this as a retryable generation failure, never substitute stub
    content (CONTENT: LLM_GEN, no stub pass).
    """
    if not isinstance(raw, dict):
        raise PlacementItemsError("placement items payload must be an object")

    written_raw = raw.get("written")
    if not isinstance(written_raw, list) or len(written_raw) != WRITTEN_ITEM_COUNT:
        raise PlacementItemsError(
            f"written must contain exactly {WRITTEN_ITEM_COUNT} items"
        )
    written = tuple(
        _parse_choice_item(item, context=f"written[{i}]")
        for i, item in enumerate(written_raw)
    )

    listening_raw = raw.get("listening")
    if not isinstance(listening_raw, dict):
        raise PlacementItemsError("listening must be an object")
    script = listening_raw.get("script")
    if not isinstance(script, str) or not script.strip():
        raise PlacementItemsError("listening.script must be a non-empty string")
    questions_raw = listening_raw.get("questions")
    if (
        not isinstance(questions_raw, list)
        or len(questions_raw) != LISTENING_QUESTION_COUNT
    ):
        raise PlacementItemsError(
            f"listening.questions must contain exactly {LISTENING_QUESTION_COUNT} items"
        )
    questions = tuple(
        _parse_choice_item(item, context=f"listening.questions[{i}]")
        for i, item in enumerate(questions_raw)
    )
    listening = ListeningContent(script=script.strip(), questions=questions)

    speaking_raw = raw.get("speaking_prompts")
    if (
        not isinstance(speaking_raw, list)
        or len(speaking_raw) != SPEAKING_PROMPT_COUNT
        or not all(isinstance(p, str) and p.strip() for p in speaking_raw)
    ):
        raise PlacementItemsError(
            f"speaking_prompts must contain exactly {SPEAKING_PROMPT_COUNT} non-empty strings"
        )
    speaking_prompts = tuple(p.strip() for p in speaking_raw)

    return PlacementItems(
        written=written, listening=listening, speaking_prompts=speaking_prompts
    )


def placement_items_to_storage(items: PlacementItems) -> dict[str, Any]:
    """Full server-side dict (incl. `correct_index`) for SQLite persistence."""
    return {
        "written": [
            {
                "prompt": i.prompt,
                "options": list(i.options),
                "correct_index": i.correct_index,
            }
            for i in items.written
        ],
        "listening": {
            "script": items.listening.script,
            "questions": [
                {
                    "prompt": q.prompt,
                    "options": list(q.options),
                    "correct_index": q.correct_index,
                }
                for q in items.listening.questions
            ],
        },
        "speaking_prompts": list(items.speaking_prompts),
    }


# Keys that must never appear on the wire — even if a future build path
# accidentally copies storage fields into the public projection.
_ANSWER_KEY_FIELDS = frozenset({"correct_index", "script"})


def _scrub_answer_keys(value: Any) -> Any:
    """Defense-in-depth: drop answer-key fields from any nested mapping/list."""
    if isinstance(value, dict):
        return {
            key: _scrub_answer_keys(item)
            for key, item in value.items()
            if key not in _ANSWER_KEY_FIELDS
        }
    if isinstance(value, list):
        return [_scrub_answer_keys(item) for item in value]
    return value


def placement_items_public(items: PlacementItems) -> dict[str, Any]:
    """Client-safe dict — strips `correct_index` and the raw script/answer key
    so placement cannot be gamed by reading the wire payload."""
    public = {
        "written": [
            {"prompt": i.prompt, "options": list(i.options)} for i in items.written
        ],
        "listening": {
            "questions": [
                {"prompt": q.prompt, "options": list(q.options)}
                for q in items.listening.questions
            ],
        },
        "speaking_prompts": list(items.speaking_prompts),
    }
    return _scrub_answer_keys(public)


def score_choice_answers(items: Sequence[ChoiceItem], answers: Sequence[int]) -> float:
    """Fraction of `answers[i] == items[i].correct_index`. Raises on length mismatch."""
    if len(answers) != len(items):
        raise ValueError("answers length must match items length")
    if not items:
        return 0.0
    correct = sum(1 for item, ans in zip(items, answers) if ans == item.correct_index)
    return round(correct / len(items), 4)


def score_speaking_transcript(transcript: str, prompts: Sequence[str]) -> float:
    """MVP aggregate presence score (word count vs. expected turns).

    Not pronunciation/intonation scoring — that is explicitly deferred to
    Epic 3.7. This only rewards a real, substantive STT capture.
    """
    words = len(transcript.split())
    target = max(1, len(prompts)) * _SPEAKING_WORDS_PER_PROMPT
    return round(min(1.0, words / target), 4)
