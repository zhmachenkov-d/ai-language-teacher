"""LLM port: generate the placement written/listening/speaking item set."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable


class LlmGenerationError(RuntimeError):
    """LLM call failed (missing config / network / auth / unparseable response).

    Callers must surface this as a retryable error with a Settings path —
    never fabricate a placement item set to paper over it (CONTENT: LLM_GEN).
    """


@runtime_checkable
class LlmPort(Protocol):
    """Adapters must call a real LLM and return its raw JSON-shaped response.

    The returned dict is validated by `domain.placement.parse_placement_items`
    — adapters must not pre-validate/shape it beyond JSON parsing.
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
