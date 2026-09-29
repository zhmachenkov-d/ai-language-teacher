"""Voice port: local-first TTS synthesis + STT transcription (no cloud fallback)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class VoiceUnavailableError(RuntimeError):
    """Local Voice engine missing or failed.

    Callers must surface this as a retryable error (retry and/or Settings) —
    never award a fake listening/speaking pass (VOICE: REAL_STT / LISTENING_AUDIO: TTS).
    """


@runtime_checkable
class VoicePort(Protocol):
    """Local speech I/O. Adapters must perform real synthesis/transcription —
    no bundled fixture audio, no fabricated transcript."""

    def synthesize_speech(self, text: str) -> bytes:
        """Return WAV audio bytes for `text` via a local TTS engine."""
        ...

    def transcribe_audio(self, audio_bytes: bytes, *, mime_type: str) -> str:
        """Return the transcript for locally captured `audio_bytes` via a local STT engine."""
        ...
