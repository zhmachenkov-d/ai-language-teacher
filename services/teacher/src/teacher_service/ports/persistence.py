"""Persistence port: Learner + LivingPlan create/load/update."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from teacher_service.domain.learner import Learner
    from teacher_service.domain.living_plan import (
        LessonRecord,
        LivingPlan,
        LivingPlanProjection,
    )


@runtime_checkable
class PersistencePort(Protocol):
    """SQLite-backed Learner + LivingPlan store (AD-7 / AD-10)."""

    def create_learner(self, learner: Learner) -> Learner:
        """Persist a new Learner and return it."""
        ...

    def load_learner(self) -> Learner | None:
        """Load the single Learner row, or None if none exists yet."""
        ...

    def update_learner(self, learner: Learner) -> Learner:
        """Replace the single Learner row and return it."""
        ...

    def create_living_plan_atomic(
        self,
        plan: LivingPlan,
        lessons: tuple[LessonRecord, ...],
    ) -> LivingPlanProjection:
        """One txn: insert LivingPlan + lessons and set learner.plan_complete=true.

        `UNIQUE(learner_id)` makes concurrent creates race-safe (caller may
        reload on IntegrityError for idempotency).
        """
        ...

    def load_living_plan(self, learner_id: str) -> LivingPlanProjection | None:
        """Load the LivingPlan + lessons for a learner, or None if absent."""
        ...
