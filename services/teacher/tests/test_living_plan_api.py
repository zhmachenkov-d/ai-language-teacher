"""HTTP I/O matrix for POST/GET /living-plan (Story 2.4).

LLM is injected; WEEK_FILL uses fixture `now` via create_app(now_provider=...).
"""

from __future__ import annotations

import secrets
import sqlite3
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from teacher_service.adapters.api.app import create_app
from teacher_service.adapters.api.auth import AUTH_TOKEN_ENV
from teacher_service.adapters.config import SECRET_LLM_API_KEY, FileConfig
from teacher_service.adapters.persistence import SqliteStore
from teacher_service.ports.llm import LlmGenerationError


def _valid_propose_payload() -> dict[str, Any]:
    return {
        "paths": [
            {
                "id": "conv",
                "title": "Conversation first",
                "summary": "Speak early, grammar lightly",
                "recommended": True,
            },
            {
                "id": "grammar",
                "title": "Grammar foundation",
                "summary": "Solid structure then talk",
                "recommended": False,
            },
        ],
        "goals": ["Hold a 10-minute work conversation"],
        "focus": "Spoken fluency at work",
        "upcoming_topics": ["Introductions", "Meetings", "Email replies"],
    }


class FakeLlmPort:
    def __init__(
        self,
        propose: dict | None = None,
        *,
        propose_error: Exception | None = None,
    ) -> None:
        self.propose = propose if propose is not None else _valid_propose_payload()
        self.propose_error = propose_error
        self.propose_calls = 0

    def generate_placement_items(
        self,
        *,
        target_language: str,
        l1: str,
        interests: Sequence[str],
        emphasis: Sequence[str],
    ) -> dict[str, Any]:
        raise AssertionError("placement LLM must not be called in living-plan tests")

    def propose_learning_paths(
        self,
        *,
        target_language: str,
        l1: str,
        goals: Sequence[str],
        desired_outcome: Sequence[str],
        interests: Sequence[str],
        emphasis: Sequence[str],
        difficulty: str,
    ) -> dict[str, Any]:
        self.propose_calls += 1
        if self.propose_error is not None:
            raise self.propose_error
        return self.propose


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
    cfg.set_secret(SECRET_LLM_API_KEY, "test-llm-key")
    return cfg


@pytest.fixture
def fixture_now() -> datetime:
    # Monday 2026-03-02 06:00 UTC = 09:00 Europe/Moscow
    return datetime(2026, 3, 2, 6, 0, tzinfo=timezone.utc)


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def make_client(
    config: FileConfig,
    auth_token: str,
    *,
    llm: FakeLlmPort | None = None,
    now: datetime | None = None,
) -> tuple[TestClient, FakeLlmPort]:
    fake = llm or FakeLlmPort()
    fixed = now or datetime(2026, 3, 2, 6, 0, tzinfo=timezone.utc)
    client = TestClient(
        create_app(
            auth_token=auth_token,
            config=config,
            llm=fake,
            now_provider=lambda: fixed,
        )
    )
    return client, fake


def _seed_placement_ready(
    client: TestClient,
    auth_token: str,
    *,
    listening_score: float = 0.6,
    speaking_score: float = 0.7,
    weekly_slots: list[dict] | None = None,
) -> None:
    slots = weekly_slots if weekly_slots is not None else [
        {"weekday": 0, "start_minute": 600},  # Mon 10:00 — after fixture 09:00 local
        {"weekday": 2, "start_minute": 1080},  # Wed 18:00
    ]
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
            "timezone": "Europe/Moscow",
            "weekly_slots": slots,
            "intake_step": "complete",
        },
        headers=_auth_header(auth_token),
    )
    client.patch(
        "/learner",
        json={
            "consent_mic": True,
            "consent_ai": True,
            "consent_privacy": True,
            "consent_complete": True,
        },
        headers=_auth_header(auth_token),
    )
    # Bypass placement stage machinery: write scores + FLAG via store.
    store = SqliteStore(client.app.state.config.sqlite_path())
    learner = store.load_learner()
    assert learner is not None
    from dataclasses import replace

    from teacher_service.domain.placement import PLACEMENT_STAGE_COMPLETE

    updated = replace(
        learner,
        placement_stage=PLACEMENT_STAGE_COMPLETE,
        placement_listening_generated=True,
        placement_listening_played=True,
        placement_listening_score=listening_score,
        placement_speaking_transcript="enough words here for a speaking sample",
        placement_speaking_score=speaking_score,
        placement_complete=True,
    )
    store.update_learner(updated)


def _assert_projection_matches(actual: dict, expected: dict) -> None:
    """Assert create/GET/idempotent responses share curriculum + lesson wire fields."""
    assert actual["id"] == expected["id"]
    assert actual["goals"] == expected["goals"]
    assert actual["focus"] == expected["focus"]
    assert actual["upcoming_topics"] == expected["upcoming_topics"]
    assert actual["proposed_paths"] == expected["proposed_paths"]
    assert len(actual["lessons"]) == len(expected["lessons"])
    for got, want in zip(actual["lessons"], expected["lessons"], strict=True):
        assert got["id"] == want["id"]
        assert got["scheduled_at"] == want["scheduled_at"]
        assert got["timezone"] == want["timezone"]


class TestLivingPlanApi:
    def test_ready_create_returns_projection_and_sets_flag(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, llm = make_client(config, auth_token, now=fixture_now)
        _seed_placement_ready(client, auth_token)

        response = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        )
        assert response.status_code == 200
        body = response.json()
        assert body["selected_path_id"] == "conv"
        assert body["difficulty"] == "intermediate"  # avg(0.6,0.7)=0.65
        assert body["revisable"] is True
        assert body["target_language"] == "en"
        assert body["l1"] == "ru"
        assert body["focus"] == "Spoken fluency at work"
        assert len(body["proposed_paths"]) == 2
        assert len(body["lessons"]) == 2
        for lesson in body["lessons"]:
            assert set(lesson.keys()) == {"id", "scheduled_at", "timezone"}
            assert lesson["timezone"] == "Europe/Moscow"
            assert lesson["scheduled_at"].endswith("Z")
        assert llm.propose_calls == 1

        profile = client.get("/learner", headers=_auth_header(auth_token)).json()
        assert profile["plan_complete"] is True

    def test_idempotent_post_skips_re_llm(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, llm = make_client(config, auth_token, now=fixture_now)
        _seed_placement_ready(client, auth_token)
        first = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        ).json()
        second = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        )
        assert second.status_code == 200
        _assert_projection_matches(second.json(), first)
        assert llm.propose_calls == 1

    def test_post_rejects_non_empty_body(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, _ = make_client(config, auth_token, now=fixture_now)
        _seed_placement_ready(client, auth_token)
        response = client.post(
            "/living-plan",
            json={"path_id": "conv"},
            headers=_auth_header(auth_token),
        )
        assert response.status_code == 422
        assert response.json()["code"] == "validation_error"

    def test_llm_config_missing(
        self, data_dir: Path, auth_token: str, fixture_now: datetime
    ) -> None:
        cfg = FileConfig(data_dir)
        cfg.ensure_layout()
        # no LLM secret
        client, llm = make_client(cfg, auth_token, now=fixture_now)
        _seed_placement_ready(client, auth_token)
        response = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        )
        assert response.status_code == 422
        assert response.json()["code"] == "llm_config_missing"
        assert llm.propose_calls == 0
        profile = client.get("/learner", headers=_auth_header(auth_token)).json()
        assert profile["plan_complete"] is False
        store = SqliteStore(cfg.sqlite_path())
        learner = store.load_learner()
        assert learner is not None
        assert store.load_living_plan(learner.id) is None

    def test_llm_generation_failed(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, llm = make_client(
            config,
            auth_token,
            llm=FakeLlmPort(propose_error=LlmGenerationError("boom")),
            now=fixture_now,
        )
        _seed_placement_ready(client, auth_token)
        response = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        )
        assert response.status_code == 422
        assert response.json()["code"] == "llm_generation_failed"
        assert response.json()["retryable"] is True
        profile = client.get("/learner", headers=_auth_header(auth_token)).json()
        assert profile["plan_complete"] is False
        store = SqliteStore(config.sqlite_path())
        learner = store.load_learner()
        assert learner is not None
        assert store.load_living_plan(learner.id) is None

    def test_invalid_llm_json_is_generation_failed(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, _ = make_client(
            config,
            auth_token,
            llm=FakeLlmPort(propose={"paths": []}),
            now=fixture_now,
        )
        _seed_placement_ready(client, auth_token)
        response = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        )
        assert response.status_code == 422
        assert response.json()["code"] == "llm_generation_failed"
        profile = client.get("/learner", headers=_auth_header(auth_token)).json()
        assert profile["plan_complete"] is False
        store = SqliteStore(config.sqlite_path())
        learner = store.load_learner()
        assert learner is not None
        assert store.load_living_plan(learner.id) is None

    def test_schedule_unusable_empty_slots(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, llm = make_client(config, auth_token, now=fixture_now)
        _seed_placement_ready(client, auth_token)
        store = SqliteStore(config.sqlite_path())
        from dataclasses import replace

        learner = store.load_learner()
        assert learner is not None
        store.update_learner(replace(learner, weekly_slots=()))
        response = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        )
        assert response.status_code == 422
        assert response.json()["code"] == "schedule_unusable"
        assert llm.propose_calls == 0
        profile = client.get("/learner", headers=_auth_header(auth_token)).json()
        assert profile["plan_complete"] is False
        learner = store.load_learner()
        assert learner is not None
        assert store.load_living_plan(learner.id) is None

    def test_schedule_unusable_zero_hits_in_window(
        self, config: FileConfig, auth_token: str
    ) -> None:
        # now == this week's Mon 09:00 MSK → current omitted; next week == window end → omit
        now = datetime(2026, 3, 2, 6, 0, 0, tzinfo=timezone.utc)
        client, llm = make_client(config, auth_token, now=now)
        _seed_placement_ready(
            client,
            auth_token,
            weekly_slots=[{"weekday": 0, "start_minute": 9 * 60}],
        )
        response = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        )
        assert response.status_code == 422
        assert response.json()["code"] == "schedule_unusable"
        assert llm.propose_calls == 0
        profile = client.get("/learner", headers=_auth_header(auth_token)).json()
        assert profile["plan_complete"] is False
        store = SqliteStore(config.sqlite_path())
        learner = store.load_learner()
        assert learner is not None
        assert store.load_living_plan(learner.id) is None

    def test_schedule_unusable_invalid_timezone(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, llm = make_client(config, auth_token, now=fixture_now)
        _seed_placement_ready(client, auth_token)
        store = SqliteStore(config.sqlite_path())
        from dataclasses import replace

        learner = store.load_learner()
        assert learner is not None
        store.update_learner(replace(learner, timezone="Not/A_Zone"))
        response = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        )
        assert response.status_code == 422
        assert response.json()["code"] == "schedule_unusable"
        assert llm.propose_calls == 0

    def test_placement_incomplete(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, llm = make_client(config, auth_token, now=fixture_now)
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
                "timezone": "Europe/Moscow",
                "weekly_slots": [{"weekday": 0, "start_minute": 600}],
                "intake_step": "complete",
                "consent_mic": True,
                "consent_ai": True,
                "consent_privacy": True,
                "consent_complete": True,
            },
            headers=_auth_header(auth_token),
        )
        response = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        )
        assert response.status_code == 422
        assert response.json()["code"] == "placement_incomplete"
        assert llm.propose_calls == 0

    def test_placement_scores_missing(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, llm = make_client(config, auth_token, now=fixture_now)
        _seed_placement_ready(client, auth_token)
        store = SqliteStore(config.sqlite_path())
        from dataclasses import replace

        learner = store.load_learner()
        assert learner is not None
        store.update_learner(replace(learner, placement_listening_score=None))
        response = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        )
        assert response.status_code == 422
        assert response.json()["code"] == "placement_scores_missing"
        assert llm.propose_calls == 0

    def test_get_resume(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, _ = make_client(config, auth_token, now=fixture_now)
        _seed_placement_ready(client, auth_token)
        created = client.post(
            "/living-plan", json={}, headers=_auth_header(auth_token)
        ).json()
        response = client.get("/living-plan", headers=_auth_header(auth_token))
        assert response.status_code == 200
        _assert_projection_matches(response.json(), created)

    def test_get_without_flag_404(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, _ = make_client(config, auth_token, now=fixture_now)
        _seed_placement_ready(client, auth_token)
        response = client.get("/living-plan", headers=_auth_header(auth_token))
        assert response.status_code == 404
        assert response.json()["code"] == "living_plan_not_found"

    def test_get_flag_without_plan_500(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, _ = make_client(config, auth_token, now=fixture_now)
        _seed_placement_ready(client, auth_token)
        store = SqliteStore(config.sqlite_path())
        from dataclasses import replace

        learner = store.load_learner()
        assert learner is not None
        store.update_learner(replace(learner, plan_complete=True))
        response = client.get("/living-plan", headers=_auth_header(auth_token))
        assert response.status_code == 500
        assert response.json()["code"] == "plan_inconsistent"

    def test_atomic_unique_learner(
        self, config: FileConfig, auth_token: str, fixture_now: datetime
    ) -> None:
        client, _ = make_client(config, auth_token, now=fixture_now)
        _seed_placement_ready(client, auth_token)
        client.post("/living-plan", json={}, headers=_auth_header(auth_token))
        store = SqliteStore(config.sqlite_path())
        learner = store.load_learner()
        assert learner is not None
        conn = sqlite3.connect(config.sqlite_path())
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO living_plan ("
                "id, learner_id, goals_json, focus, upcoming_topics_json, "
                "difficulty, selected_path_id, proposed_paths_json, revisable, "
                "target_language, l1"
                ") VALUES (?, ?, '[]', 'x', '[]', 'beginner', 'a', '[]', 1, 'en', 'ru')",
                ("other-id", learner.id),
            )
            conn.commit()
        conn.close()
