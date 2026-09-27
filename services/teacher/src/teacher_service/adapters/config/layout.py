"""File-backed Config adapter: OS app-data layout and secret files."""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path

from platformdirs import user_data_dir

DATA_DIR_ENV = "TEACHER_DATA_DIR"
APP_NAME = "ai-language-teacher"
APP_AUTHOR = None

SQLITE_FILENAME = "teacher.sqlite"
SECRETS_DIRNAME = "secrets"
VOICE_MODELS_DIRNAME = "voice-models"

SECRET_BEARER_TOKEN = "bearer_token"
SECRET_LLM_API_KEY = "llm_api_key"
SECRET_TELEGRAM_BOT_TOKEN = "telegram_bot_token"

_KNOWN_SECRETS = frozenset(
    {
        SECRET_BEARER_TOKEN,
        SECRET_LLM_API_KEY,
        SECRET_TELEGRAM_BOT_TOKEN,
    }
)

_DIR_MODE = 0o700
_FILE_MODE = 0o600


def resolve_data_dir(*, override: str | Path | None = None) -> Path:
    """Resolve the learner data directory (override → env → platformdirs)."""
    if override is not None:
        raw = str(override).strip()
        if not raw:
            raise ValueError("data dir override must be a non-empty path")
        return Path(raw).expanduser().resolve()
    env_raw = os.environ.get(DATA_DIR_ENV)
    if isinstance(env_raw, str) and env_raw.strip():
        return Path(env_raw.strip()).expanduser().resolve()
    return Path(user_data_dir(APP_NAME, APP_AUTHOR)).resolve()


class FileConfig:
    """ConfigPort implementation using one OS app-data directory."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self._root = resolve_data_dir(override=data_dir)

    def data_dir(self) -> Path:
        return self._root

    def sqlite_path(self) -> Path:
        return self._root / SQLITE_FILENAME

    def secrets_dir(self) -> Path:
        return self._root / SECRETS_DIRNAME

    def voice_models_dir(self) -> Path:
        return self._root / VOICE_MODELS_DIRNAME

    def ensure_layout(self) -> None:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
            self.secrets_dir().mkdir(parents=True, exist_ok=True)
            self.voice_models_dir().mkdir(parents=True, exist_ok=True)
            sqlite = self.sqlite_path()
            if not sqlite.exists():
                sqlite.touch()
            if os.name != "nt":
                os.chmod(self._root, _DIR_MODE)
                os.chmod(self.secrets_dir(), _DIR_MODE)
                os.chmod(self.voice_models_dir(), _DIR_MODE)
                if sqlite.exists():
                    os.chmod(sqlite, _FILE_MODE)
        except OSError as exc:
            raise RuntimeError(
                f"failed to create learner data layout under {self._root}"
            ) from exc

    def get_secret(self, name: str) -> str | None:
        self._validate_secret_name(name)
        path = self.secrets_dir() / name
        self._reject_symlink_escape(path)
        if not path.is_file():
            return None
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise RuntimeError(f"failed to read secret {name!r}") from exc
        value = raw.strip()
        return value if value else None

    def set_secret(self, name: str, value: str) -> None:
        self._validate_secret_name(name)
        cleaned = value.strip() if isinstance(value, str) else ""
        if not cleaned:
            raise ValueError(f"secret {name!r} must be a non-empty string")
        self.ensure_layout()
        path = self.secrets_dir() / name
        self._reject_symlink_escape(path)
        tmp_path: Path | None = None
        try:
            fd, tmp_name = tempfile.mkstemp(
                prefix=f".{name}.",
                dir=self.secrets_dir(),
            )
            tmp_path = Path(tmp_name)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(cleaned + "\n")
            if os.name != "nt":
                os.chmod(tmp_path, _FILE_MODE)
            os.replace(tmp_path, path)
            tmp_path = None
        except OSError as exc:
            raise RuntimeError(f"failed to write secret {name!r}") from exc
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

    def _reject_symlink_escape(self, path: Path) -> None:
        if path.exists() or path.is_symlink():
            if path.resolve().parent != self.secrets_dir().resolve():
                raise ValueError(
                    f"secret path escapes secrets directory: {path}"
                )

    @staticmethod
    def _validate_secret_name(name: str) -> None:
        if name not in _KNOWN_SECRETS:
            raise ValueError(
                f"unknown secret name {name!r}; "
                f"expected one of {sorted(_KNOWN_SECRETS)}"
            )


def secret_file_mode(path: Path) -> int:
    """Return the permission bits for a secret file (tests)."""
    return stat.S_IMODE(path.stat().st_mode)
