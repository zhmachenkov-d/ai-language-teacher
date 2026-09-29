"""LLM adapter: OpenAI-compatible `/chat/completions` for placement + paths.

Uses only the stdlib HTTP client so no extra runtime dependency is needed.
Never fabricates items/paths on failure — raises `LlmGenerationError` so the
API layer can surface a retryable error (CONTENT: LLM_GEN / NFR3).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from teacher_service.ports.llm import LlmGenerationError

if TYPE_CHECKING:
    from teacher_service.ports.config import ConfigPort

BASE_URL_ENV = "TEACHER_LLM_BASE_URL"
MODEL_ENV = "TEACHER_LLM_MODEL"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
_TIMEOUT_SECONDS = 30

# NFR1: never reference surname/postal address/email/phone in LLM-bound context.
_PLACEMENT_SYSTEM_PROMPT = (
    "You write an English placement test for an adult Russian-speaking learner. "
    "Reply with strict JSON only (no prose, no markdown fences) matching exactly: "
    '{"written": [{"prompt": string, "options": [string, ...3-5], '
    '"correct_index": integer}, ... exactly 5 items], '
    '"listening": {"script": string (a short spoken passage, 60-120 words), '
    '"questions": [{"prompt": string, "options": [string, ...3-5], '
    '"correct_index": integer}, ... exactly 3 items] (comprehension questions '
    "about the script, not the script itself)}, "
    '"speaking_prompts": [string, ... exactly 3] (short spoken dialogue prompts '
    "inviting a free-form spoken answer)}. "
    "Never ask for or reference the learner's surname, postal address, email, "
    "or phone number."
)

_PATHS_SYSTEM_PROMPT = (
    "You propose learning paths for an adult Russian-speaking English learner. "
    "Reply with strict JSON only (no prose, no markdown fences) matching exactly: "
    '{"paths": [{"id": string, "title": string, "summary": string, '
    '"recommended": boolean}, ... exactly 2 or 3 paths] '
    "(exactly one path must have recommended=true), "
    '"goals": [string, ... at least 1], '
    '"focus": string, '
    '"upcoming_topics": [string, ... at least 1]}. '
    "Curriculum fields (goals/focus/upcoming_topics) describe the selected "
    "recommended path's first weeks. "
    "Never ask for or reference the learner's surname, postal address, email, "
    "or phone number."
)


class OpenAiLlmAdapter:
    """Calls an OpenAI-compatible `/chat/completions` endpoint using the
    Config-stored `llm_api_key` secret. Base URL/model are overridable via
    env for compatible self-hosted/alternate providers."""

    def __init__(self, config: ConfigPort) -> None:
        self._config = config

    def generate_placement_items(
        self,
        *,
        target_language: str,
        l1: str,
        interests: Sequence[str],
        emphasis: Sequence[str],
    ) -> dict[str, Any]:
        user_prompt = (
            f"Target language: {target_language}. Learner native language: {l1}. "
            f"Learner interests: {', '.join(interests) or 'general'}. "
            f"Learner emphasis: {', '.join(emphasis) or 'balanced'}. "
            "Generate one placement item set now."
        )
        return self._chat_json(
            system=_PLACEMENT_SYSTEM_PROMPT,
            user=user_prompt,
            temperature=0.4,
        )

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
        # Intake prefs only — never address_as / age / contact fields (NFR1).
        user_prompt = (
            f"Target language: {target_language}. Learner native language: {l1}. "
            f"Difficulty band: {difficulty}. "
            f"Goals: {', '.join(goals) or 'general progress'}. "
            f"Desired outcome: {', '.join(desired_outcome) or 'confident conversation'}. "
            f"Interests: {', '.join(interests) or 'general'}. "
            f"Emphasis: {', '.join(emphasis) or 'balanced'}. "
            "Propose 2 or 3 learning paths and curriculum for the recommended path."
        )
        return self._chat_json(
            system=_PATHS_SYSTEM_PROMPT,
            user=user_prompt,
            temperature=0.5,
        )

    def _chat_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
    ) -> dict[str, Any]:
        from teacher_service.adapters.config import SECRET_LLM_API_KEY

        api_key = self._config.get_secret(SECRET_LLM_API_KEY)
        if not api_key:
            raise LlmGenerationError("LLM API key is not configured")

        base_url = os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL).rstrip("/")
        model = os.environ.get(MODEL_ENV, DEFAULT_MODEL)
        body = json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
                raw = response.read()
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise LlmGenerationError(f"LLM request failed: {exc}") from exc

        try:
            payload = json.loads(raw)
            content = payload["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LlmGenerationError(f"LLM returned an unparseable response: {exc}") from exc
        if not isinstance(parsed, dict):
            raise LlmGenerationError("LLM response content was not a JSON object")
        return parsed
