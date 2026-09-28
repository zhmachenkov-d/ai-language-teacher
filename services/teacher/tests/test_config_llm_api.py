"""HTTP -> Config I/O matrix for GET/PUT /config/llm (Story 1.6 SECRET_API)."""

from __future__ import annotations

import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from teacher_service.adapters.api.app import create_app
from teacher_service.adapters.api.auth import AUTH_TOKEN_ENV
from teacher_service.adapters.config import SECRET_BEARER_TOKEN, SECRET_LLM_API_KEY, FileConfig


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


def test_get_llm_config_unconfigured_by_default(
    client: TestClient, auth_token: str
) -> None:
    response = client.get("/config/llm", headers=_auth_header(auth_token))
    assert response.status_code == 200
    assert response.json() == {"configured": False}


def test_put_llm_config_persists_via_config_and_masks_response(
    client: TestClient, auth_token: str, config: FileConfig
) -> None:
    key = "sk-test-not-for-prod-0001"
    response = client.put(
        "/config/llm",
        json={"llm_api_key": key},
        headers=_auth_header(auth_token),
    )
    assert response.status_code == 200
    assert response.json() == {"configured": True}
    assert key not in response.text

    # Persisted only via Config; raw value never appears in the HTTP response.
    assert config.get_secret(SECRET_LLM_API_KEY) == key

    # Reopen: GET reports configured true without ever echoing the secret.
    reopened = client.get("/config/llm", headers=_auth_header(auth_token))
    assert reopened.status_code == 200
    assert reopened.json() == {"configured": True}
    assert key not in reopened.text


@pytest.mark.parametrize("blank_key", ["", "   ", "\t\n"])
def test_put_llm_config_rejects_blank_key(
    client: TestClient, auth_token: str, config: FileConfig, blank_key: str
) -> None:
    response = client.put(
        "/config/llm",
        json={"llm_api_key": blank_key},
        headers=_auth_header(auth_token),
    )
    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"code", "message", "retryable"}
    assert body["code"] == "validation_error"
    assert body["retryable"] is False
    # Config unchanged — no secret persisted for a rejected write.
    assert config.get_secret(SECRET_LLM_API_KEY) is None


def test_put_llm_config_missing_field_is_422(
    client: TestClient, auth_token: str
) -> None:
    response = client.put(
        "/config/llm", json={}, headers=_auth_header(auth_token)
    )
    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"code", "message", "retryable"}


def test_get_llm_config_without_token_rejected(client: TestClient) -> None:
    response = client.get("/config/llm")
    assert response.status_code == 401
    body = response.json()
    assert set(body) == {"code", "message", "retryable"}
    assert body["code"] == "unauthorized"


def test_put_llm_config_without_token_rejected_and_config_unchanged(
    client: TestClient, config: FileConfig
) -> None:
    response = client.put("/config/llm", json={"llm_api_key": "sk-should-not-persist"})
    assert response.status_code == 401
    assert config.get_secret(SECRET_LLM_API_KEY) is None


def test_put_llm_config_wrong_token_rejected(
    client: TestClient, config: FileConfig
) -> None:
    wrong = secrets.token_urlsafe(24)
    response = client.put(
        "/config/llm",
        json={"llm_api_key": "sk-should-not-persist"},
        headers=_auth_header(wrong),
    )
    assert response.status_code == 401
    assert config.get_secret(SECRET_LLM_API_KEY) is None


def test_bearer_remint_rejects_prior_token_on_config_llm(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rotating the Config bearer invalidates the prior token for /config/llm too."""
    config = FileConfig(data_dir)
    config.ensure_layout()
    old_bearer = secrets.token_urlsafe(24)
    config.set_secret(SECRET_BEARER_TOKEN, old_bearer)

    old_app_client = TestClient(create_app(config=config))
    ok = old_app_client.get("/config/llm", headers=_auth_header(old_bearer))
    assert ok.status_code == 200

    # Remint: rotate the Config bearer (simulates host remint on next start).
    new_bearer = secrets.token_urlsafe(24)
    config.set_secret(SECRET_BEARER_TOKEN, new_bearer)
    new_app_client = TestClient(create_app(config=config))

    rejected = new_app_client.get("/config/llm", headers=_auth_header(old_bearer))
    assert rejected.status_code == 401
    accepted = new_app_client.get("/config/llm", headers=_auth_header(new_bearer))
    assert accepted.status_code == 200
