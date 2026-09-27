"""Local Bearer token auth for the loopback HTTP API."""

from __future__ import annotations

import hmac
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from teacher_service.ports.config import ConfigPort

AUTH_TOKEN_ENV = "TEACHER_AUTH_TOKEN"

_NO_TOKEN_MSG = (
    "auth token required: pass auth_token, set non-empty "
    f"{AUTH_TOKEN_ENV}, or store bearer_token via Config"
)


class AuthSettings:
    """Auth secret for one app instance (arg, env, or Config)."""

    def __init__(self, token: str) -> None:
        cleaned = token.strip() if isinstance(token, str) else ""
        if not cleaned:
            raise ValueError(_NO_TOKEN_MSG)
        self.token = cleaned


def load_auth_token_from_env() -> str | None:
    """Return stripped env token, or None if unset/whitespace-only."""
    raw = os.environ.get(AUTH_TOKEN_ENV)
    if not isinstance(raw, str):
        return None
    token = raw.strip()
    return token if token else None


def resolve_auth_token(
    auth_token: str | None = None,
    *,
    config: ConfigPort | None = None,
) -> str:
    """Resolve Bearer token: explicit arg → env → Config secret → fail closed.

    When ``auth_token`` is not ``None``, it wins (tests). Empty/whitespace env
    counts as unset and falls through to Config.
    """
    if auth_token is not None:
        cleaned = auth_token.strip() if isinstance(auth_token, str) else ""
        if not cleaned:
            raise ValueError(_NO_TOKEN_MSG)
        return cleaned

    env_token = load_auth_token_from_env()
    if env_token is not None:
        return env_token

    from teacher_service.adapters.config import SECRET_BEARER_TOKEN

    if config is None:
        from teacher_service.adapters.config import FileConfig

        config = FileConfig()

    secret = config.get_secret(SECRET_BEARER_TOKEN)
    if secret is not None:
        cleaned = secret.strip()
        if cleaned:
            return cleaned

    raise ValueError(_NO_TOKEN_MSG)


def tokens_match(presented: str, expected: str) -> bool:
    """Constant-time (non-early-exit) compare that tolerates unequal lengths."""
    presented_bytes = presented.encode("utf-8")
    expected_bytes = expected.encode("utf-8")
    if len(presented_bytes) != len(expected_bytes):
        # Burn a compare so length mismatch is not a pure early return.
        hmac.compare_digest(expected_bytes, expected_bytes)
        return False
    return hmac.compare_digest(presented_bytes, expected_bytes)
