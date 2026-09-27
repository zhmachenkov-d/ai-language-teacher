"""Config port: learner data-dir layout and named secrets."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ConfigPort(Protocol):
    """OS app-data layout + secret get/set (AD-4 / AD-18)."""

    def data_dir(self) -> Path:
        """Resolved learner data directory root."""
        ...

    def sqlite_path(self) -> Path:
        """Path to the SQLite database file under the data directory."""
        ...

    def secrets_dir(self) -> Path:
        """Directory for secret files (single-user permissions)."""
        ...

    def voice_models_dir(self) -> Path:
        """Reserved voice-model cache subdirectory."""
        ...

    def ensure_layout(self) -> None:
        """Create data dir, secrets dir, voice-models dir, and SQLite file path."""
        ...

    def get_secret(self, name: str) -> str | None:
        """Return a named secret or None if absent. Never logs the value."""
        ...

    def set_secret(self, name: str, value: str) -> None:
        """Persist a named secret with single-user file permissions."""
        ...
