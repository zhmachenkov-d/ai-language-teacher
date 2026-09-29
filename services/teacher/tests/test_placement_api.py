"""HTTP I/O matrix for placement endpoints: /placement/items, /placement/listening/audio,
/placement/speaking/transcribe, and PATCH /learner placement fields.

LLM/Voice are injected as fake test doubles (same DI pattern as `store`/`config`)
so this suite needs no network or audio hardware. Domain-level gating rigor is
covered separately in `test_placement_domain.py`.
"""

from __future__ import annotations

import base64
import secrets
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from teacher_service.adapters.api.app import create_app
from teacher_service.adapters.api.auth import AUTH_TOKEN_ENV
from teacher_service.adapters.config import SECRET_LLM_API_KEY, FileConfig
from teacher_service.adapters.persistence import SqliteStore
from teacher_service.ports.llm import LlmGenerationError
from teacher_service.ports.voice import VoiceUnavailableError


def _valid_raw_items() -> dict:
    return {
        "written": [
            {"prompt": f"Q{i}", "options": ["a", "b", "c"], "correct_index": 0}
            for i in range(5)
        ],
        "listening": {
            "script": "A short passage about daily life.",
            "questions": [
                {"prompt": f"L{i}", "options": ["a", "b", "c"], "correct_index": 1}
                for i in range(3)
            ],
        },
        "speaking_prompts": ["Tell me about your day.", "Describe your job.", "Plans?"],
    }


class FakeLlmPort:
    def __init__(self, raw: dict | None = None, error: Exception | None = None) -> None:
        self.raw = raw if raw is not None else _valid_raw_items()
        self.error = error
        self.calls = 0

    def generate_placement_items(
        self,
        *,
        target_language: str,
        l1: str,
        interests: Sequence[str],
        emphasis: Sequence[str],
    ) -> dict[str, Any]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.raw

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
        raise AssertionError("living-plan LLM must not be called in placement tests")


class FakeVoicePort:
    def __init__(
        self,
        *,
        audio: bytes = b"RIFF-fake-wav-bytes",
        transcript: str = "hello there this is a real transcript with enough words "
        * 3,
        synth_error: Exception | None = None,
        transcribe_error: Exception | None = None,
    ) -> None:
        self.audio = audio
        self.transcript = transcript
        self.synth_error = synth_error
        self.transcribe_error = transcribe_error
        self.synth_calls = 0
        self.transcribe_calls = 0

    def synthesize_speech(self, text: str) -> bytes:
        self.synth_calls += 1
        if self.synth_error is not None:
            raise self.synth_error
        return self.audio

    def transcribe_audio(self, audio_bytes: bytes, *, mime_type: str) -> str:
        self.transcribe_calls += 1
        if self.transcribe_error is not None:
            raise self.transcribe_error
        return self.transcript


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


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def make_client(
    config: FileConfig,
    auth_token: str,
    *,
    llm: FakeLlmPort | None = None,
    voice: FakeVoicePort | None = None,
) -> TestClient:
    return TestClient(
        create_app(
            auth_token=auth_token,
            config=config,
            llm=llm or FakeLlmPort(),
            voice=voice or FakeVoicePort(),
        )
    )


def _seed_consent_complete(client: TestClient, auth_token: str) -> None:
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
            "weekly_slots": [{"weekday": 0, "start_minute": 540}],
            "intake_step": "complete",
        },
        headers=_auth_header(auth_token),
    )
    response = client.patch(
        "/learner",
        json={
            "consent_mic": True,
            "consent_ai": True,
            "consent_privacy": True,
            "consent_complete": True,
        },
        headers=_auth_header(auth_token),
    )
    assert response.status_code == 200


class TestGeneratePlacementItems:
    def test_requires_consent(self, config: FileConfig, auth_token: str) -> None:
        client = make_client(config, auth_token)
        response = client.post("/placement/items", headers=_auth_header(auth_token))
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "placement_requires_consent"
        assert body["retryable"] is False

    def test_missing_llm_config_blocks_with_retryable_error(
        self, config: FileConfig, auth_token: str
    ) -> None:
        client = make_client(config, auth_token)
        _seed_consent_complete(client, auth_token)
        response = client.post("/placement/items", headers=_auth_header(auth_token))
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "llm_config_missing"
        assert body["retryable"] is True

    def test_generation_failure_is_retryable_no_fake_items(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        llm = FakeLlmPort(error=LlmGenerationError("network down"))
        client = make_client(config, auth_token, llm=llm)
        _seed_consent_complete(client, auth_token)
        response = client.post("/placement/items", headers=_auth_header(auth_token))
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "llm_generation_failed"
        assert body["retryable"] is True
        # No item set was persisted from the failed attempt.
        again = client.get("/learner", headers=_auth_header(auth_token))
        assert again.json()["placement_items"] is None

    def test_malformed_llm_payload_is_retryable_no_fake_items(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        llm = FakeLlmPort(raw={"written": []})  # malformed shape
        client = make_client(config, auth_token, llm=llm)
        _seed_consent_complete(client, auth_token)
        response = client.post("/placement/items", headers=_auth_header(auth_token))
        assert response.status_code == 422
        assert response.json()["code"] == "llm_generation_failed"

    def test_happy_path_returns_public_items_without_answer_key(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        client = make_client(config, auth_token)
        _seed_consent_complete(client, auth_token)
        response = client.post("/placement/items", headers=_auth_header(auth_token))
        assert response.status_code == 200
        body = response.json()
        assert len(body["written"]) == 5
        assert "correct_index" not in body["written"][0]
        assert "script" not in body["listening"]
        assert len(body["speaking_prompts"]) == 3

    def test_one_item_set_per_run_llm_called_once(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        llm = FakeLlmPort()
        client = make_client(config, auth_token, llm=llm)
        _seed_consent_complete(client, auth_token)
        first = client.post("/placement/items", headers=_auth_header(auth_token))
        second = client.post("/placement/items", headers=_auth_header(auth_token))
        assert first.status_code == second.status_code == 200
        assert first.json() == second.json()
        assert llm.calls == 1

    def test_get_and_patch_learner_never_leak_answer_key(
        self, config: FileConfig, auth_token: str
    ) -> None:
        """Once items exist, neither GET nor PATCH /learner may echo `correct_index`
        or the listening `script` — only the public projection is wire-visible."""
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        client = make_client(config, auth_token)
        _seed_consent_complete(client, auth_token)
        client.post("/placement/items", headers=_auth_header(auth_token))

        get_body = client.get("/learner", headers=_auth_header(auth_token)).json()
        assert "correct_index" not in get_body["placement_items"]["written"][0]
        assert (
            "correct_index"
            not in get_body["placement_items"]["listening"]["questions"][0]
        )
        assert "script" not in get_body["placement_items"]["listening"]

        patch_response = client.patch(
            "/learner",
            json={
                "placement_written_answers": [0, 0, 0, 0, 0],
                "placement_stage": "listening",
            },
            headers=_auth_header(auth_token),
        )
        assert patch_response.status_code == 200
        patch_body = patch_response.json()
        assert "correct_index" not in patch_body["placement_items"]["written"][0]
        assert (
            "correct_index"
            not in patch_body["placement_items"]["listening"]["questions"][0]
        )
        assert "script" not in patch_body["placement_items"]["listening"]


class TestListeningAudio:
    def test_requires_consent(self, config: FileConfig, auth_token: str) -> None:
        client = make_client(config, auth_token)
        response = client.post(
            "/placement/listening/audio", headers=_auth_header(auth_token)
        )
        assert response.status_code == 422
        assert response.json()["code"] == "placement_requires_consent"

    def test_requires_items_first(self, config: FileConfig, auth_token: str) -> None:
        client = make_client(config, auth_token)
        _seed_consent_complete(client, auth_token)
        response = client.post(
            "/placement/listening/audio", headers=_auth_header(auth_token)
        )
        assert response.status_code == 422
        assert response.json()["code"] == "placement_items_missing"

    def test_voice_unavailable_is_retryable_no_fake_pass(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        voice = FakeVoicePort(synth_error=VoiceUnavailableError("espeak-ng not found"))
        client = make_client(config, auth_token, voice=voice)
        _seed_consent_complete(client, auth_token)
        client.post("/placement/items", headers=_auth_header(auth_token))
        response = client.post(
            "/placement/listening/audio", headers=_auth_header(auth_token)
        )
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "voice_unavailable"
        assert body["retryable"] is True
        learner = client.get("/learner", headers=_auth_header(auth_token)).json()
        assert learner["placement_listening_generated"] is False

    def test_happy_path_returns_audio_and_marks_generated(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        client = make_client(config, auth_token)
        _seed_consent_complete(client, auth_token)
        client.post("/placement/items", headers=_auth_header(auth_token))
        response = client.post(
            "/placement/listening/audio", headers=_auth_header(auth_token)
        )
        assert response.status_code == 200
        body = response.json()
        assert base64.b64decode(body["audio_base64"]) == b"RIFF-fake-wav-bytes"
        assert body["mime_type"] == "audio/wav"
        learner = client.get("/learner", headers=_auth_header(auth_token)).json()
        assert learner["placement_listening_generated"] is True


class TestSpeakingTranscribe:
    def test_requires_consent(self, config: FileConfig, auth_token: str) -> None:
        client = make_client(config, auth_token)
        response = client.post(
            "/placement/speaking/transcribe",
            json={
                "audio_base64": base64.b64encode(b"x").decode(),
                "mime_type": "audio/webm",
            },
            headers=_auth_header(auth_token),
        )
        assert response.status_code == 422
        assert response.json()["code"] == "placement_requires_consent"

    def test_requires_items_first(self, config: FileConfig, auth_token: str) -> None:
        client = make_client(config, auth_token)
        _seed_consent_complete(client, auth_token)
        response = client.post(
            "/placement/speaking/transcribe",
            json={
                "audio_base64": base64.b64encode(b"x").decode(),
                "mime_type": "audio/webm",
            },
            headers=_auth_header(auth_token),
        )
        assert response.status_code == 422
        assert response.json()["code"] == "placement_items_missing"

    def test_oversized_audio_payload_is_rejected(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        client = make_client(config, auth_token)
        _seed_consent_complete(client, auth_token)
        client.post("/placement/items", headers=_auth_header(auth_token))
        oversized = base64.b64encode(b"x" * 100).decode() * 40_000  # > 4M chars
        response = client.post(
            "/placement/speaking/transcribe",
            json={"audio_base64": oversized, "mime_type": "audio/webm"},
            headers=_auth_header(auth_token),
        )
        assert response.status_code == 422
        assert response.json()["code"] == "validation_error"

    def test_mic_stt_failure_is_retryable_no_fake_pass(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        voice = FakeVoicePort(
            transcribe_error=VoiceUnavailableError("local STT engine not found")
        )
        client = make_client(config, auth_token, voice=voice)
        _seed_consent_complete(client, auth_token)
        client.post("/placement/items", headers=_auth_header(auth_token))
        response = client.post(
            "/placement/speaking/transcribe",
            json={
                "audio_base64": base64.b64encode(b"x").decode(),
                "mime_type": "audio/webm",
            },
            headers=_auth_header(auth_token),
        )
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "voice_unavailable"
        assert body["retryable"] is True
        learner = client.get("/learner", headers=_auth_header(auth_token)).json()
        assert learner["placement_speaking_transcript"] is None

    def test_happy_path_persists_transcript_and_score(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        client = make_client(config, auth_token)
        _seed_consent_complete(client, auth_token)
        client.post("/placement/items", headers=_auth_header(auth_token))
        response = client.post(
            "/placement/speaking/transcribe",
            json={
                "audio_base64": base64.b64encode(b"x").decode(),
                "mime_type": "audio/webm",
            },
            headers=_auth_header(auth_token),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["placement_speaking_transcript"]
        assert body["placement_speaking_score"] is not None


class TestPlacementCompleteEndToEnd:
    def _generate_and_prime(self, client: TestClient, auth_token: str) -> None:
        _seed_consent_complete(client, auth_token)
        client.post("/placement/items", headers=_auth_header(auth_token))

    def test_text_only_complete_rejected_missing_listening_and_speaking(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        client = make_client(config, auth_token)
        self._generate_and_prime(client, auth_token)
        client.patch(
            "/learner",
            json={"placement_written_answers": [0, 0, 0, 0, 0]},
            headers=_auth_header(auth_token),
        )
        response = client.patch(
            "/learner",
            json={"placement_complete": True},
            headers=_auth_header(auth_token),
        )
        assert response.status_code == 422
        body = response.json()
        assert set(body) == {"code", "message", "retryable"}
        assert body["code"] in {
            "placement_listening_incomplete",
            "placement_speaking_incomplete",
        }
        stored = client.get("/learner", headers=_auth_header(auth_token)).json()
        assert stored["placement_complete"] is False

    def test_full_flow_reaches_placement_complete(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        client = make_client(config, auth_token)
        self._generate_and_prime(client, auth_token)

        written = client.patch(
            "/learner",
            json={
                "placement_written_answers": [0, 0, 0, 0, 0],
                "placement_stage": "listening",
            },
            headers=_auth_header(auth_token),
        )
        assert written.status_code == 200
        assert written.json()["placement_written_score"] == 1.0

        audio = client.post(
            "/placement/listening/audio", headers=_auth_header(auth_token)
        )
        assert audio.status_code == 200

        listening = client.patch(
            "/learner",
            json={
                "placement_listening_played": True,
                "placement_listening_answers": [1, 1, 1],
                "placement_stage": "speaking",
            },
            headers=_auth_header(auth_token),
        )
        assert listening.status_code == 200
        assert listening.json()["placement_listening_score"] == 1.0

        transcribe = client.post(
            "/placement/speaking/transcribe",
            json={
                "audio_base64": base64.b64encode(b"x").decode(),
                "mime_type": "audio/webm",
            },
            headers=_auth_header(auth_token),
        )
        assert transcribe.status_code == 200

        complete = client.patch(
            "/learner",
            json={"placement_stage": "complete", "placement_complete": True},
            headers=_auth_header(auth_token),
        )
        assert complete.status_code == 200
        body = complete.json()
        assert body["placement_complete"] is True
        assert body["placement_stage"] == "complete"

    def test_resume_persists_stage_across_reload(
        self, config: FileConfig, auth_token: str
    ) -> None:
        config.set_secret(SECRET_LLM_API_KEY, "sk-test")
        client = make_client(config, auth_token)
        self._generate_and_prime(client, auth_token)
        client.patch(
            "/learner",
            json={
                "placement_written_answers": [0, 0, 0, 0, 0],
                "placement_stage": "listening",
            },
            headers=_auth_header(auth_token),
        )
        reopened = client.get("/learner", headers=_auth_header(auth_token))
        assert reopened.json()["placement_stage"] == "listening"
        assert reopened.json()["placement_items"] is not None


def test_legacy_learner_without_placement_columns_gets_defaults(
    data_dir: Path, auth_token: str
) -> None:
    """Pre-2.3 learner tables gain placement columns with safe defaults on open."""
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
                timezone TEXT NOT NULL,
                intake_step TEXT NOT NULL DEFAULT 'greeting',
                consent_mic INTEGER NOT NULL DEFAULT 0,
                consent_telegram INTEGER NOT NULL DEFAULT 0,
                consent_ai INTEGER NOT NULL DEFAULT 0,
                consent_privacy INTEGER NOT NULL DEFAULT 0,
                consent_complete INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            "INSERT INTO learner (id, target_language, l1, timezone) "
            "VALUES ('legacy-placement', 'en', 'ru', 'UTC')"
        )
        conn.commit()

    store = SqliteStore(db_path)
    loaded = store.load_learner()
    assert loaded is not None
    assert loaded.placement_stage == "briefing"
    assert loaded.placement_items is None
    assert loaded.placement_written_answers == ()
    assert loaded.placement_written_score is None
    assert loaded.placement_listening_generated is False
    assert loaded.placement_listening_played is False
    assert loaded.placement_listening_answers == ()
    assert loaded.placement_listening_score is None
    assert loaded.placement_speaking_transcript is None
    assert loaded.placement_speaking_score is None
    assert loaded.placement_complete is False

    client = TestClient(create_app(auth_token=auth_token, config=config, store=store))
    response = client.get("/learner", headers=_auth_header(auth_token))
    assert response.status_code == 200
    body = response.json()
    assert body["placement_stage"] == "briefing"
    assert body["placement_complete"] is False
    assert body["placement_items"] is None


def test_corrupt_placement_stage_coerces_to_briefing(
    data_dir: Path, auth_token: str
) -> None:
    """Unknown placement_stage values from SQLite fall back to briefing on load."""
    import sqlite3

    config = FileConfig(data_dir)
    config.ensure_layout()
    db_path = config.sqlite_path()
    store = SqliteStore(db_path)
    # Ensure full schema exists, then poison the stage enum.
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO learner (id, target_language, l1, timezone, placement_stage) "
            "VALUES ('corrupt-stage', 'en', 'ru', 'UTC', 'not-a-stage')"
        )
        conn.commit()

    loaded = store.load_learner()
    assert loaded is not None
    assert loaded.placement_stage == "briefing"
