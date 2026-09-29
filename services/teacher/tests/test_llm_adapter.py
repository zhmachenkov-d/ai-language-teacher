"""Thin unit smoke for production `OpenAiLlmAdapter`.

Placement/living-plan API suites inject Fake* ports — fabricate-on-error in the
real adapter would stay green. These tests execute the real class with a mocked
HTTP transport (no live OpenAI).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import URLError

import pytest
from teacher_service.adapters.config import SECRET_LLM_API_KEY, FileConfig
from teacher_service.adapters.llm import BASE_URL_ENV, OpenAiLlmAdapter
from teacher_service.ports.llm import LlmGenerationError


@pytest.fixture
def config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FileConfig:
    root = tmp_path / "teacher-data"
    monkeypatch.setenv("TEACHER_DATA_DIR", str(root))
    cfg = FileConfig(root)
    cfg.ensure_layout()
    return cfg


class _FakeHttpResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> _FakeHttpResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _chat_payload(content: dict[str, Any]) -> dict[str, Any]:
    return {"choices": [{"message": {"content": json.dumps(content)}}]}


def test_generate_placement_items_parses_json_content(
    config: FileConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    config.set_secret(SECRET_LLM_API_KEY, "sk-test")
    monkeypatch.setenv(BASE_URL_ENV, "https://llm.test/v1")

    expected = {
        "written": [{"prompt": "q", "options": ["a", "b", "c"], "correct_index": 0}],
        "listening": {
            "script": "hello world " * 10,
            "questions": [
                {"prompt": "lq", "options": ["a", "b", "c"], "correct_index": 1}
            ],
        },
        "speaking_prompts": ["say one", "say two", "say three"],
    }
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeHttpResponse:
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _FakeHttpResponse(_chat_payload(expected))

    monkeypatch.setattr(
        "urllib.request.urlopen", fake_urlopen
    )

    adapter = OpenAiLlmAdapter(config)
    result = adapter.generate_placement_items(
        target_language="en",
        l1="ru",
        interests=["tech"],
        emphasis=["speaking"],
    )
    assert result == expected
    assert captured["url"] == "https://llm.test/v1/chat/completions"
    assert captured["authorization"] == "Bearer sk-test"
    system = captured["body"]["messages"][0]["content"].lower()
    user = captured["body"]["messages"][1]["content"].lower()
    # NFR1: ban instruction stays in system; user prompt carries intake prefs only.
    assert "never ask for or reference the learner's surname" in system
    assert "address_as" not in user
    assert "@" not in user


def test_propose_learning_paths_parses_json_content(
    config: FileConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    config.set_secret(SECRET_LLM_API_KEY, "sk-test")
    expected = {
        "paths": [
            {
                "id": "a",
                "title": "A",
                "summary": "s",
                "recommended": True,
            },
            {
                "id": "b",
                "title": "B",
                "summary": "s",
                "recommended": False,
            },
        ],
        "goals": ["g"],
        "focus": "speaking",
        "upcoming_topics": ["t1"],
    }

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=0: _FakeHttpResponse(_chat_payload(expected)),
    )

    adapter = OpenAiLlmAdapter(config)
    result = adapter.propose_learning_paths(
        target_language="en",
        l1="ru",
        goals=["travel"],
        desired_outcome=["chat"],
        interests=["food"],
        emphasis=["listening"],
        difficulty="A2",
    )
    assert result == expected


def test_missing_api_key_raises_without_fabricating(config: FileConfig) -> None:
    adapter = OpenAiLlmAdapter(config)
    with pytest.raises(LlmGenerationError, match="not configured"):
        adapter.generate_placement_items(
            target_language="en", l1="ru", interests=[], emphasis=[]
        )


def test_network_failure_raises_without_fabricating(
    config: FileConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    config.set_secret(SECRET_LLM_API_KEY, "sk-test")

    def boom(*_args: Any, **_kwargs: Any) -> Any:
        raise URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", boom)

    adapter = OpenAiLlmAdapter(config)
    with pytest.raises(LlmGenerationError, match="LLM request failed"):
        adapter.propose_learning_paths(
            target_language="en",
            l1="ru",
            goals=[],
            desired_outcome=[],
            interests=[],
            emphasis=[],
            difficulty="B1",
        )


def test_unparseable_response_raises_without_fabricating(
    config: FileConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    config.set_secret(SECRET_LLM_API_KEY, "sk-test")

    class BadResponse:
        def read(self) -> bytes:
            return b'{"choices":[{"message":{"content":"not-json"}}]}'

        def __enter__(self) -> BadResponse:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_a, **_k: BadResponse(),
    )

    adapter = OpenAiLlmAdapter(config)
    with pytest.raises(LlmGenerationError, match="unparseable"):
        adapter.generate_placement_items(
            target_language="en", l1="ru", interests=[], emphasis=[]
        )
