"""Loopback HTTP API auth, health, and error-shape tests (Story 1.2)."""

from __future__ import annotations

import secrets

import pytest
from fastapi.testclient import TestClient

from teacher_service.adapters.api.app import LOOPBACK_HOST, create_app
from teacher_service.adapters.api.auth import AUTH_TOKEN_ENV, tokens_match
from teacher_service.adapters.api.cli import main as cli_main


@pytest.fixture
def auth_token() -> str:
    return secrets.token_urlsafe(32)


@pytest.fixture
def client(auth_token: str) -> TestClient:
    return TestClient(create_app(auth_token=auth_token))


def test_health_with_valid_bearer(client: TestClient, auth_token: str) -> None:
    response = client.get(
        "/health", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok"}
    assert auth_token not in response.text
    assert AUTH_TOKEN_ENV not in response.text
    assert "Authorization" not in response.text


def test_health_without_token_rejected(client: TestClient, auth_token: str) -> None:
    response = client.get("/health")
    assert response.status_code == 401
    body = response.json()
    assert set(body) == {"code", "message", "retryable"}
    assert body["code"] == "unauthorized"
    assert body["retryable"] is False
    assert auth_token not in response.text
    assert AUTH_TOKEN_ENV not in response.text
    assert "Bearer" not in response.text


def test_health_wrong_token_rejected(client: TestClient, auth_token: str) -> None:
    wrong = secrets.token_urlsafe(32)
    response = client.get(
        "/health", headers={"Authorization": f"Bearer {wrong}"}
    )
    assert response.status_code == 401
    body = response.json()
    assert set(body) == {"code", "message", "retryable"}
    assert body["code"] == "unauthorized"
    assert auth_token not in response.text
    assert wrong not in response.text
    assert AUTH_TOKEN_ENV not in response.text


def test_tokens_match_constant_time_semantics() -> None:
    token = "a" * 32
    assert tokens_match(token, token) is True
    assert tokens_match("b" * 32, token) is False
    assert tokens_match("short", token) is False
    assert tokens_match("", token) is False


def test_create_app_reads_env_token(monkeypatch: pytest.MonkeyPatch) -> None:
    token = secrets.token_urlsafe(24)
    monkeypatch.setenv(AUTH_TOKEN_ENV, token)
    with TestClient(create_app()) as env_client:
        ok = env_client.get(
            "/health", headers={"Authorization": f"Bearer {token}"}
        )
        assert ok.status_code == 200
        denied = env_client.get("/health")
        assert denied.status_code == 401
        assert token not in denied.text


def test_create_app_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(AUTH_TOKEN_ENV, raising=False)
    with pytest.raises(ValueError, match=AUTH_TOKEN_ENV):
        create_app()


def test_unauthenticated_non_health_rejected(
    client: TestClient, auth_token: str
) -> None:
    for path in ("/openapi.json", "/nope"):
        response = client.get(path)
        assert response.status_code == 401, path
        body = response.json()
        assert set(body) == {"code", "message", "retryable"}
        assert body["code"] == "unauthorized"
        assert auth_token not in response.text
        assert AUTH_TOKEN_ENV not in response.text
        assert "detail" not in body


def test_authenticated_unknown_path_shaped_404(
    client: TestClient, auth_token: str
) -> None:
    response = client.get(
        "/nope", headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"code", "message", "retryable"}
    assert "detail" not in body
    assert auth_token not in response.text


def test_whitespace_env_token_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(AUTH_TOKEN_ENV, "   \t\n")
    with pytest.raises(ValueError, match=AUTH_TOKEN_ENV):
        create_app()


def test_cli_rejects_non_loopback_host(
    monkeypatch: pytest.MonkeyPatch, auth_token: str
) -> None:
    monkeypatch.setenv(AUTH_TOKEN_ENV, auth_token)
    with pytest.raises(SystemExit) as excinfo:
        cli_main(["--host", "0.0.0.0"])
    assert excinfo.value.code == 2


def test_cli_rejects_non_default_port(
    monkeypatch: pytest.MonkeyPatch, auth_token: str
) -> None:
    monkeypatch.setenv(AUTH_TOKEN_ENV, auth_token)
    with pytest.raises(SystemExit) as excinfo:
        cli_main(["--port", "9000"])
    assert excinfo.value.code == 2


def test_cli_binds_loopback_fixed_port(
    monkeypatch: pytest.MonkeyPatch, auth_token: str
) -> None:
    monkeypatch.setenv(AUTH_TOKEN_ENV, auth_token)
    calls: list[dict[str, object]] = []

    def fake_run(app: object, **kwargs: object) -> None:
        calls.append({"app": app, **kwargs})

    monkeypatch.setattr(
        "teacher_service.adapters.api.cli.uvicorn.run", fake_run
    )
    cli_main([])
    assert len(calls) == 1
    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["port"] == 8765


def test_cli_requires_env_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(AUTH_TOKEN_ENV, raising=False)
    with pytest.raises(SystemExit) as excinfo:
        cli_main([])
    assert excinfo.value.code == 1


def test_loopback_host_constant() -> None:
    assert LOOPBACK_HOST == "127.0.0.1"
