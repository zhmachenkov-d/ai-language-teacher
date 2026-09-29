"""HTTP -> Config I/O matrix for GET/PUT /config/voice (cloud key status only)."""

from __future__ import annotations

import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from teacher_service.adapters.api.app import create_app
from teacher_service.adapters.api.auth import AUTH_TOKEN_ENV
from teacher_service.adapters.config import (
    SECRET_BEARER_TOKEN,
    SECRET_CLOUD_VOICE_API_KEY,
    FileConfig,
)
from teacher_service.adapters.voice import (
    CloudVoiceAdapter,
    LocalThenCloudVoice,
    LocalVoiceAdapter,
)
from teacher_service.ports.voice import VoiceUnavailableError


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "teacher-data"
    monkeypatch.setenv("TEACHER_DATA_DIR", str(root))
    monkeypatch.delenv(AUTH_TOKEN_ENV, raising=False)
    return root


@pytest.fixture
def auth_token() -> str:
    return secrets.token_urlsafe(24)


@pytest.fixture
def config(data_dir: Path) -> FileConfig:
    cfg = FileConfig(data_dir)
    cfg.ensure_layout()
    return cfg


@pytest.fixture
def client(config: FileConfig, auth_token: str) -> TestClient:
    return TestClient(create_app(auth_token=auth_token, config=config))


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_get_voice_config_unconfigured_by_default(
    client: TestClient, auth_token: str
) -> None:
    response = client.get("/config/voice", headers=_auth_header(auth_token))
    assert response.status_code == 200
    assert response.json() == {"configured": False}


def test_put_voice_config_persists_via_config_and_masks_response(
    client: TestClient, auth_token: str, config: FileConfig
) -> None:
    key = "cv-test-not-for-prod-0001"
    response = client.put(
        "/config/voice",
        json={"cloud_voice_api_key": key},
        headers=_auth_header(auth_token),
    )
    assert response.status_code == 200
    assert response.json() == {"configured": True}
    assert key not in response.text

    assert config.get_secret(SECRET_CLOUD_VOICE_API_KEY) == key

    reopened = client.get("/config/voice", headers=_auth_header(auth_token))
    assert reopened.status_code == 200
    assert reopened.json() == {"configured": True}
    assert key not in reopened.text


@pytest.mark.parametrize("blank_key", ["", "   ", "\t\n"])
def test_put_voice_config_rejects_blank_key(
    client: TestClient, auth_token: str, config: FileConfig, blank_key: str
) -> None:
    response = client.put(
        "/config/voice",
        json={"cloud_voice_api_key": blank_key},
        headers=_auth_header(auth_token),
    )
    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"code", "message", "retryable"}
    assert body["code"] == "validation_error"
    assert body["retryable"] is False
    assert config.get_secret(SECRET_CLOUD_VOICE_API_KEY) is None


def test_put_voice_config_missing_field_is_422(
    client: TestClient, auth_token: str
) -> None:
    response = client.put("/config/voice", json={}, headers=_auth_header(auth_token))
    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"code", "message", "retryable"}


def test_get_voice_config_without_token_rejected(client: TestClient) -> None:
    response = client.get("/config/voice")
    assert response.status_code == 401
    body = response.json()
    assert set(body) == {"code", "message", "retryable"}
    assert body["code"] == "unauthorized"


def test_put_voice_config_without_token_rejected_and_config_unchanged(
    client: TestClient, config: FileConfig
) -> None:
    response = client.put(
        "/config/voice", json={"cloud_voice_api_key": "cv-should-not-persist"}
    )
    assert response.status_code == 401
    assert config.get_secret(SECRET_CLOUD_VOICE_API_KEY) is None


def test_put_voice_config_wrong_token_rejected(
    client: TestClient, config: FileConfig
) -> None:
    wrong = secrets.token_urlsafe(24)
    response = client.put(
        "/config/voice",
        json={"cloud_voice_api_key": "cv-should-not-persist"},
        headers=_auth_header(wrong),
    )
    assert response.status_code == 401
    assert config.get_secret(SECRET_CLOUD_VOICE_API_KEY) is None


def test_bearer_remint_rejects_prior_token_on_config_voice(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = FileConfig(data_dir)
    config.ensure_layout()
    old_bearer = secrets.token_urlsafe(24)
    config.set_secret(SECRET_BEARER_TOKEN, old_bearer)

    old_app_client = TestClient(create_app(config=config))
    ok = old_app_client.get("/config/voice", headers=_auth_header(old_bearer))
    assert ok.status_code == 200

    new_bearer = secrets.token_urlsafe(24)
    config.set_secret(SECRET_BEARER_TOKEN, new_bearer)
    new_app_client = TestClient(create_app(config=config))

    rejected = new_app_client.get("/config/voice", headers=_auth_header(old_bearer))
    assert rejected.status_code == 401
    accepted = new_app_client.get("/config/voice", headers=_auth_header(new_bearer))
    assert accepted.status_code == 200


def test_config_voice_runtime_error_returns_shaped_500(
    client: TestClient,
    auth_token: str,
    config: FileConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(_name: str) -> None:
        raise RuntimeError("failed to read secret 'cloud_voice_api_key'")

    monkeypatch.setattr(config, "get_secret", boom)
    response = client.get("/config/voice", headers=_auth_header(auth_token))
    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "config_error"
    assert body["retryable"] is True
    assert "failed to read secret" in body["message"]


class _InjectedFakeVoice:
    """DI override — must be used as-is; composite must not be forced."""

    def __init__(self) -> None:
        self.synth_calls = 0

    def synthesize_speech(self, text: str) -> bytes:
        self.synth_calls += 1
        raise VoiceUnavailableError("injected fake — not composite")

    def transcribe_audio(self, audio_bytes: bytes, *, mime_type: str) -> str:
        raise VoiceUnavailableError("injected fake — not composite")


def test_create_app_voice_di_override_skips_composite(
    config: FileConfig, auth_token: str
) -> None:
    fake = _InjectedFakeVoice()
    app = create_app(auth_token=auth_token, config=config, voice=fake)
    assert app.state.voice is fake
    assert not isinstance(app.state.voice, LocalThenCloudVoice)
    with pytest.raises(VoiceUnavailableError, match="injected fake"):
        app.state.voice.synthesize_speech("x")
    assert fake.synth_calls == 1


def test_create_app_default_voice_is_local_then_cloud(
    config: FileConfig, auth_token: str
) -> None:
    app = create_app(auth_token=auth_token, config=config)
    assert isinstance(app.state.voice, LocalThenCloudVoice)
    assert isinstance(app.state.voice._local, LocalVoiceAdapter)
    assert isinstance(app.state.voice._cloud, CloudVoiceAdapter)
    assert app.state.voice._cloud._config is config
    assert app.state.voice._config is config
