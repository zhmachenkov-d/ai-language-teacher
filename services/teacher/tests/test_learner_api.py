"""HTTP I/O matrix for GET/PATCH /learner (Story 2.1 intake)."""

from __future__ import annotations

import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from teacher_service.adapters.api.app import create_app
from teacher_service.adapters.api.auth import AUTH_TOKEN_ENV
from teacher_service.adapters.config import FileConfig
from teacher_service.adapters.persistence import SqliteStore
from teacher_service.domain.learner import (
    DEFAULT_L1,
    DEFAULT_TARGET_LANGUAGE,
    DEFAULT_TIMEZONE,
    INTAKE_STEP_COMPLETE,
    INTAKE_STEP_GOALS,
    INTAKE_STEP_GREETING,
    get_or_create_learner,
)


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


def test_get_learner_creates_defaults(
    client: TestClient, auth_token: str, config: FileConfig
) -> None:
    response = client.get("/learner", headers=_auth_header(auth_token))
    assert response.status_code == 200
    body = response.json()
    assert body["target_language"] == DEFAULT_TARGET_LANGUAGE
    assert body["l1"] == DEFAULT_L1
    assert body["timezone"] == DEFAULT_TIMEZONE
    assert body["address_as"] is None
    assert body["age"] is None
    assert body["goals"] == []
    assert body["desired_outcome"] == []
    assert body["interests"] == []
    assert body["emphasis"] == []
    assert body["lesson_duration_minutes"] is None
    assert body["weekly_slots"] == []
    assert body["intake_step"] == INTAKE_STEP_GREETING
    assert body["id"]

    store = SqliteStore(config.sqlite_path())
    assert store.load_learner() is not None


def test_patch_greeting_and_advance(
    client: TestClient, auth_token: str
) -> None:
    response = client.patch(
        "/learner",
        json={
            "address_as": "Алекс",
            "age": 28,
            "intake_step": INTAKE_STEP_GOALS,
        },
        headers=_auth_header(auth_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["address_as"] == "Алекс"
    assert body["age"] == 28
    assert body["intake_step"] == INTAKE_STEP_GOALS

    again = client.get("/learner", headers=_auth_header(auth_token))
    assert again.json()["address_as"] == "Алекс"
    assert again.json()["intake_step"] == INTAKE_STEP_GOALS


def test_patch_prefs_duration_schedule_complete(
    client: TestClient, auth_token: str
) -> None:
    client.patch(
        "/learner",
        json={"address_as": "Саша", "age": 30, "intake_step": "goals"},
        headers=_auth_header(auth_token),
    )
    client.patch(
        "/learner",
        json={
            "goals": ["Работа / карьера", "Свой фокус"],
            "desired_outcome": ["Уверенный разговор"],
            "intake_step": "interests",
        },
        headers=_auth_header(auth_token),
    )
    client.patch(
        "/learner",
        json={
            "interests": ["Технологии"],
            "emphasis": ["Говорение", "Грамматика"],
            "intake_step": "duration",
        },
        headers=_auth_header(auth_token),
    )
    client.patch(
        "/learner",
        json={"lesson_duration_minutes": 45, "intake_step": "schedule"},
        headers=_auth_header(auth_token),
    )
    response = client.patch(
        "/learner",
        json={
            "timezone": "Europe/Moscow",
            "weekly_slots": [
                {"weekday": 0, "start_minute": 540},
                {"weekday": 0, "start_minute": 540},  # duplicate → coalesce
                {"weekday": 2, "start_minute": 1140},
            ],
            "intake_step": INTAKE_STEP_COMPLETE,
        },
        headers=_auth_header(auth_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["lesson_duration_minutes"] == 45
    assert body["timezone"] == "Europe/Moscow"
    assert body["weekly_slots"] == [
        {"weekday": 0, "start_minute": 540},
        {"weekday": 2, "start_minute": 1140},
    ]
    assert body["intake_step"] == INTAKE_STEP_COMPLETE
    assert body["goals"] == ["Работа / карьера", "Свой фокус"]


@pytest.mark.parametrize(
    "payload",
    [
        {"address_as": "   "},
        {"age": 0},
        {"age": 121},
        {"lesson_duration_minutes": 40},
        {"weekly_slots": [{"weekday": 7, "start_minute": 0}]},
        {"weekly_slots": [{"weekday": 0, "start_minute": 1440}]},
        {"intake_step": "not-a-step"},
        {"timezone": "  "},
    ],
)
def test_patch_rejects_invalid_fields(
    client: TestClient, auth_token: str, payload: dict
) -> None:
    response = client.patch(
        "/learner", json=payload, headers=_auth_header(auth_token)
    )
    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"code", "message", "retryable"}
    assert body["code"] == "validation_error"
    assert body["retryable"] is False


def test_get_learner_without_token_rejected(client: TestClient) -> None:
    response = client.get("/learner")
    assert response.status_code == 401
    body = response.json()
    assert set(body) == {"code", "message", "retryable"}
    assert body["code"] == "unauthorized"


def test_patch_learner_without_token_rejected(
    client: TestClient, config: FileConfig
) -> None:
    response = client.patch("/learner", json={"address_as": "X", "age": 20})
    assert response.status_code == 401
    store = SqliteStore(config.sqlite_path())
    assert store.load_learner() is None


def test_health_still_works_without_learner_row(
    client: TestClient, auth_token: str, config: FileConfig
) -> None:
    ok = client.get("/health", headers=_auth_header(auth_token))
    assert ok.status_code == 200
    assert SqliteStore(config.sqlite_path()).load_learner() is None


def test_patch_rejects_complete_without_slots(
    client: TestClient, auth_token: str
) -> None:
    client.patch(
        "/learner",
        json={
            "address_as": "Саша",
            "age": 30,
            "goals": ["Учёба"],
            "desired_outcome": ["Уверенный разговор"],
            "interests": ["Технологии"],
            "emphasis": ["Говорение"],
            "lesson_duration_minutes": 45,
            "intake_step": "schedule",
        },
        headers=_auth_header(auth_token),
    )
    response = client.patch(
        "/learner",
        json={
            "timezone": "Europe/Moscow",
            "weekly_slots": [],
            "intake_step": INTAKE_STEP_COMPLETE,
        },
        headers=_auth_header(auth_token),
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert "slot" in body["message"].lower()


def test_persistence_update_roundtrip(config: FileConfig) -> None:
    store = SqliteStore(config.sqlite_path())
    learner = get_or_create_learner(store)
    from teacher_service.domain.learner import update_learner

    updated = update_learner(
        store,
        address_as="Миша",
        age=16,
        goals=["Учёба"],
        intake_step=INTAKE_STEP_GOALS,
    )
    assert updated.id == learner.id
    reloaded = store.load_learner()
    assert reloaded is not None
    assert reloaded.address_as == "Миша"
    assert reloaded.age == 16
    assert reloaded.goals == ("Учёба",)
    assert reloaded.intake_step == INTAKE_STEP_GOALS


def test_legacy_four_column_learner_migrates_intake_defaults(
    data_dir: Path, auth_token: str
) -> None:
    """Pre-2.1 learner tables gain intake columns with defaults on open."""
    import sqlite3

    config = FileConfig(data_dir)
    config.ensure_layout()
    db_path = config.sqlite_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE IF EXISTS learner")
        conn.execute(
            """
            CREATE TABLE learner (
                id TEXT PRIMARY KEY NOT NULL,
                target_language TEXT NOT NULL,
                l1 TEXT NOT NULL,
                timezone TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO learner (id, target_language, l1, timezone) "
            "VALUES ('legacy-id', 'en', 'ru', 'UTC')"
        )
        conn.commit()

    store = SqliteStore(db_path)
    loaded = store.load_learner()
    assert loaded is not None
    assert loaded.id == "legacy-id"
    assert loaded.address_as is None
    assert loaded.age is None
    assert loaded.goals == ()
    assert loaded.desired_outcome == ()
    assert loaded.interests == ()
    assert loaded.emphasis == ()
    assert loaded.lesson_duration_minutes is None
    assert loaded.weekly_slots == ()
    assert loaded.intake_step == INTAKE_STEP_GREETING

    client = TestClient(create_app(auth_token=auth_token, config=config, store=store))
    response = client.get("/learner", headers=_auth_header(auth_token))
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "legacy-id"
    assert body["intake_step"] == INTAKE_STEP_GREETING
    assert body["goals"] == []
    assert body["weekly_slots"] == []


def test_patch_rejects_complete_without_step_complete_fields(
    client: TestClient, auth_token: str
) -> None:
    response = client.patch(
        "/learner",
        json={
            "timezone": "Europe/Moscow",
            "weekly_slots": [{"weekday": 0, "start_minute": 540}],
            "intake_step": INTAKE_STEP_COMPLETE,
        },
        headers=_auth_header(auth_token),
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
