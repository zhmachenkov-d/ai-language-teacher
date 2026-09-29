"""Voice port: local-first TTS/STT with optional cloud fallback behind the same port.

Callers use only `synthesize_speech` / `transcribe_audio`. Adapters compose
local-then-cloud (AD-9); the UI never calls a cloud voice vendor directly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class VoiceUnavailableError(RuntimeError):
    """Local (and optional cloud) Voice path missing or failed.

    Callers must surface this as a retryable error (retry and/or Settings) —
    never award a fake listening/speaking pass (VOICE: REAL_STT / LISTENING_AUDIO: TTS).
    """


@runtime_checkable
class VoicePort(Protocol):
    """Speech I/O via a single port. Default stack is local-first with optional
    config-gated cloud fallback behind the same methods — no silent cloud use,
    no fabricated audio/transcript."""

    def synthesize_speech(self, text: str) -> bytes:
        """Return non-empty WAV audio bytes for `text` (local, then optional cloud)."""
        ...

    def transcribe_audio(self, audio_bytes: bytes, *, mime_type: str) -> str:
        """Return a non-empty transcript for `audio_bytes` (local, then optional cloud)."""
        ...
