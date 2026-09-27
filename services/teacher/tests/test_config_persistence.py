"""Config layout, secrets, SQLite Learner, and Bearer resolve (Story 1.3)."""

from __future__ import annotations

import os
import secrets
import stat
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from platformdirs import user_data_dir
from teacher_service.adapters.api.app import create_app
from teacher_service.adapters.api.auth import AUTH_TOKEN_ENV, resolve_auth_token
from teacher_service.adapters.api.cli import main as cli_main
from teacher_service.adapters.config import (
    APP_AUTHOR,
    APP_NAME,
    DATA_DIR_ENV,
    SECRET_BEARER_TOKEN,
    SECRET_LLM_API_KEY,
    SECRET_TELEGRAM_BOT_TOKEN,
    FileConfig,
)
from teacher_service.adapters.config.layout import secret_file_mode
from teacher_service.adapters.persistence import SqliteStore
from teacher_service.domain.learner import (
    DEFAULT_L1,
    DEFAULT_TARGET_LANGUAGE,
    DEFAULT_TIMEZONE,
    Learner,
    get_or_create_learner,
)


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "teacher-data"
    monkeypatch.setenv(DATA_DIR_ENV, str(root))
    monkeypatch.delenv(AUTH_TOKEN_ENV, raising=False)
    return root


def test_fresh_layout_and_learner_defaults(data_dir: Path) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()

    assert config.data_dir() == data_dir.resolve()
    assert config.sqlite_path().is_file()
    assert config.secrets_dir().is_dir()
    assert config.voice_models_dir().is_dir()
    assert list(config.voice_models_dir().iterdir()) == []

    store = SqliteStore(config.sqlite_path())
    learner = get_or_create_learner(store)

    assert uuid.UUID(learner.id)
    assert learner.target_language == DEFAULT_TARGET_LANGUAGE == "en"
    assert learner.l1 == DEFAULT_L1 == "ru"
    assert learner.timezone == DEFAULT_TIMEZONE == "UTC"

    again = get_or_create_learner(store)
    assert again == learner


def test_secret_persist_and_absent(data_dir: Path) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()

    assert config.get_secret(SECRET_LLM_API_KEY) is None
    assert config.get_secret(SECRET_TELEGRAM_BOT_TOKEN) is None

    llm_key = "sk-test-not-for-prod"
    tg_token = "123456:AA-test-telegram-token"
    config.set_secret(SECRET_LLM_API_KEY, llm_key)
    config.set_secret(SECRET_TELEGRAM_BOT_TOKEN, tg_token)

    assert config.get_secret(SECRET_LLM_API_KEY) == llm_key
    assert config.get_secret(SECRET_TELEGRAM_BOT_TOKEN) == tg_token

    llm_path = config.secrets_dir() / SECRET_LLM_API_KEY
    tg_path = config.secrets_dir() / SECRET_TELEGRAM_BOT_TOKEN
    if os.name != "nt":
        assert secret_file_mode(llm_path) == 0o600
        assert secret_file_mode(tg_path) == 0o600

    # Learner still loadable when LLM secret is absent.
    store = SqliteStore(config.sqlite_path())
    learner = get_or_create_learner(store)
    assert learner.id
    config2 = FileConfig(data_dir)
    assert config2.get_secret(SECRET_LLM_API_KEY) == llm_key
    # Wipe LLM secret file to prove absence does not block Learner load.
    (config.secrets_dir() / SECRET_LLM_API_KEY).unlink()
    assert config.get_secret(SECRET_LLM_API_KEY) is None
    assert get_or_create_learner(store).id == learner.id


def test_unknown_secret_name_rejected(data_dir: Path) -> None:
    config = FileConfig(data_dir)
    with pytest.raises(ValueError, match="unknown secret"):
        config.get_secret("not_a_real_secret")
    with pytest.raises(ValueError, match="unknown secret"):
        config.set_secret("not_a_real_secret", "x")


def test_bearer_via_config_health(data_dir: Path) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()
    bearer = secrets.token_urlsafe(24)
    config.set_secret(SECRET_BEARER_TOKEN, bearer)

    app = create_app(config=config)
    client = TestClient(app)
    ok = client.get("/health", headers={"Authorization": f"Bearer {bearer}"})
    assert ok.status_code == 200
    assert ok.json() == {"status": "ok"}
    assert bearer not in ok.text

    denied = client.get("/health")
    assert denied.status_code == 401
    assert bearer not in denied.text
    body = denied.json()
    assert set(body) == {"code", "message", "retryable"}


def test_env_overrides_config_bearer(data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()
    config_token = secrets.token_urlsafe(16)
    env_token = secrets.token_urlsafe(16)
    config.set_secret(SECRET_BEARER_TOKEN, config_token)
    monkeypatch.setenv(AUTH_TOKEN_ENV, env_token)

    resolved = resolve_auth_token(config=config)
    assert resolved == env_token

    app = create_app(config=config)
    client = TestClient(app)
    assert (
        client.get("/health", headers={"Authorization": f"Bearer {env_token}"}).status_code
        == 200
    )
    assert (
        client.get(
            "/health", headers={"Authorization": f"Bearer {config_token}"}
        ).status_code
        == 401
    )


def test_explicit_arg_wins_over_env_and_config(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()
    config.set_secret(SECRET_BEARER_TOKEN, "config-token-value")
    monkeypatch.setenv(AUTH_TOKEN_ENV, "env-token-value")
    arg_token = "explicit-arg-token"
    assert resolve_auth_token(arg_token, config=config) == arg_token
    app = create_app(auth_token=arg_token, config=config)
    client = TestClient(app)
    assert (
        client.get("/health", headers={"Authorization": f"Bearer {arg_token}"}).status_code
        == 200
    )


def test_whitespace_env_falls_through_to_config(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()
    bearer = secrets.token_urlsafe(20)
    config.set_secret(SECRET_BEARER_TOKEN, bearer)
    monkeypatch.setenv(AUTH_TOKEN_ENV, "   \t\n")
    assert resolve_auth_token(config=config) == bearer


def test_resolve_fails_closed_without_any_token(data_dir: Path) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()
    with pytest.raises(ValueError, match=AUTH_TOKEN_ENV):
        resolve_auth_token(config=config)


def test_cli_uses_config_bearer_without_sqlite_learner(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()
    bearer = secrets.token_urlsafe(24)
    config.set_secret(SECRET_BEARER_TOKEN, bearer)

    calls: list[dict[str, object]] = []

    def fake_run(app: object, **kwargs: object) -> None:
        calls.append({"app": app, **kwargs})

    monkeypatch.setattr("teacher_service.adapters.api.cli.uvicorn.run", fake_run)
    cli_main([])
    assert len(calls) == 1
    served = TestClient(calls[0]["app"])  # type: ignore[arg-type]
    ok = served.get("/health", headers={"Authorization": f"Bearer {bearer}"})
    assert ok.status_code == 200
    assert ok.json() == {"status": "ok"}
    # Layout may exist, but CLI must not require Learner init.
    store = SqliteStore(config.sqlite_path())
    assert store.load_learner() is None


def test_cli_fails_closed_without_token(data_dir: Path) -> None:
    FileConfig(data_dir).ensure_layout()
    with pytest.raises(SystemExit) as excinfo:
        cli_main([])
    assert excinfo.value.code == 1


def test_data_dir_env_override_isolation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(AUTH_TOKEN_ENV, raising=False)
    override = tmp_path / "override-data"
    monkeypatch.setenv(DATA_DIR_ENV, str(override))
    config = FileConfig()
    config.ensure_layout()
    assert config.data_dir() == override.resolve()
    assert (override / "secrets").is_dir()
    assert (override / "voice-models").is_dir()
    assert (override / "teacher.sqlite").is_file()


def test_default_data_dir_matches_platformdirs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(DATA_DIR_ENV, raising=False)
    expected = Path(user_data_dir(APP_NAME, APP_AUTHOR)).resolve()
    assert FileConfig().data_dir() == expected


def test_create_app_loads_bearer_from_data_dir_env(
    data_dir: Path,
) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()
    bearer = secrets.token_urlsafe(24)
    config.set_secret(SECRET_BEARER_TOKEN, bearer)

    app = create_app()
    client = TestClient(app)
    ok = client.get("/health", headers={"Authorization": f"Bearer {bearer}"})
    assert ok.status_code == 200
    assert ok.json() == {"status": "ok"}


def test_cli_ensure_layout_failure_exits_1(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(self: FileConfig) -> None:
        raise RuntimeError("failed to create learner data layout")

    monkeypatch.setattr(FileConfig, "ensure_layout", boom)
    with pytest.raises(SystemExit) as excinfo:
        cli_main([])
    assert excinfo.value.code == 1


def test_second_create_learner_raises(data_dir: Path) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()
    store = SqliteStore(config.sqlite_path())
    get_or_create_learner(store)
    duplicate = Learner(
        id=str(uuid.uuid4()),
        target_language=DEFAULT_TARGET_LANGUAGE,
        l1=DEFAULT_L1,
        timezone=DEFAULT_TIMEZONE,
    )
    with pytest.raises(ValueError, match="already exists"):
        store.create_learner(duplicate)


def test_layout_dir_modes_0700(data_dir: Path) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()
    if os.name == "nt":
        return
    for path in (config.data_dir(), config.secrets_dir(), config.voice_models_dir()):
        assert stat.S_IMODE(path.stat().st_mode) == 0o700
