"""LLM port: placement items + living-plan path proposals."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable


class LlmGenerationError(RuntimeError):
    """LLM call failed (missing config / network / auth / unparseable response).

    Callers must surface this as a retryable error with a Settings path —
    never fabricate a placement item set or learning path to paper over it.
    """


@runtime_checkable
class LlmPort(Protocol):
    """Adapters must call a real LLM and return its raw JSON-shaped response.

    Returned dicts are validated by domain parsers — adapters must not
    pre-validate/shape beyond JSON parsing.
    """

    def generate_placement_items(
        self,
        *,
        target_language: str,
        l1: str,
        interests: Sequence[str],
        emphasis: Sequence[str],
    ) -> dict[str, Any]:
        """Return one raw placement item-set payload for this learner context."""
        ...

    def propose_learning_paths(
        self,
        *,
        target_language: str,
        l1: str,
        goals: Sequence[str],
        desired_outcome: Sequence[str],
        interests: Sequence[str],
        emphasis: Sequence[str],
        difficulty: str,
    ) -> dict[str, Any]:
        """Return raw path options + curriculum for living-plan creation.

        Expected shape (validated by domain):
        `{ "paths": [{id,title,summary,recommended}, ...2-3],
           "goals": string[], "focus": string, "upcoming_topics": string[] }`.
        """
        ...
