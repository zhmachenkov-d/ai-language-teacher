"""Learner entity and get-or-create use case (via PersistencePort only)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from teacher_service.ports.persistence import PersistencePort

DEFAULT_TARGET_LANGUAGE = "en"
DEFAULT_L1 = "ru"
DEFAULT_TIMEZONE = "UTC"


@dataclass(frozen=True)
class Learner:
    """Minimal learner profile persisted in SQLite."""

    id: str
    target_language: str
    l1: str
    timezone: str


def get_or_create_learner(store: PersistencePort) -> Learner:
    """Return the existing Learner or create one with v1 defaults."""
    existing = store.load_learner()
    if existing is not None:
        return existing
    learner = Learner(
        id=str(uuid.uuid4()),
        target_language=DEFAULT_TARGET_LANGUAGE,
        l1=DEFAULT_L1,
        timezone=DEFAULT_TIMEZONE,
    )
    return store.create_learner(learner)
