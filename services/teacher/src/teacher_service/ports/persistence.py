"""Persistence port: Learner create/load/update."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from teacher_service.domain.learner import Learner


@runtime_checkable
class PersistencePort(Protocol):
    """SQLite-backed Learner store (AD-7 / AD-10)."""

    def create_learner(self, learner: Learner) -> Learner:
        """Persist a new Learner and return it."""
        ...

    def load_learner(self) -> Learner | None:
        """Load the single Learner row, or None if none exists yet."""
        ...

    def update_learner(self, learner: Learner) -> Learner:
        """Replace the single Learner row and return it."""
        ...
