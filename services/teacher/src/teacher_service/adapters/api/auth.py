"""Local Bearer token auth for the loopback HTTP API."""

from __future__ import annotations

import hmac
import os

AUTH_TOKEN_ENV = "TEACHER_AUTH_TOKEN"


class AuthSettings:
    """Auth secret for one app instance (env or test override)."""

    def __init__(self, token: str) -> None:
        cleaned = token.strip() if isinstance(token, str) else ""
        if not cleaned:
            raise ValueError(f"{AUTH_TOKEN_ENV} must be a non-empty string")
        self.token = cleaned


def load_auth_token_from_env() -> str:
    raw = os.environ.get(AUTH_TOKEN_ENV)
    token = raw.strip() if isinstance(raw, str) else ""
    if not token:
        raise ValueError(
            f"{AUTH_TOKEN_ENV} is required and must be a non-empty string"
        )
    return token


def tokens_match(presented: str, expected: str) -> bool:
    """Constant-time (non-early-exit) compare that tolerates unequal lengths."""
    presented_bytes = presented.encode("utf-8")
    expected_bytes = expected.encode("utf-8")
    if len(presented_bytes) != len(expected_bytes):
        # Burn a compare so length mismatch is not a pure early return.
        hmac.compare_digest(expected_bytes, expected_bytes)
        return False
    return hmac.compare_digest(presented_bytes, expected_bytes)
