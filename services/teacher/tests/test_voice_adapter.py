"""Unit tests for `LocalVoiceAdapter`'s command-template formatting.

A misconfigured `TEACHER_TTS_COMMAND`/`TEACHER_STT_COMMAND` (e.g. referencing an
unknown placeholder, or a stray `{`/`}`) must raise `VoiceUnavailableError` —
never bubble up a raw KeyError/ValueError past the API/UI's error handling.
"""

from __future__ import annotations

import pytest
from teacher_service.adapters.voice import LocalVoiceAdapter
from teacher_service.ports.voice import VoiceUnavailableError


def test_synthesize_speech_with_unknown_placeholder_raises_voice_unavailable() -> None:
    adapter = LocalVoiceAdapter(tts_command="echo {unknown_placeholder}")
    with pytest.raises(VoiceUnavailableError):
        adapter.synthesize_speech("hello")


def test_synthesize_speech_with_malformed_format_spec_raises_voice_unavailable() -> None:
    adapter = LocalVoiceAdapter(tts_command="echo {text_file")  # unbalanced brace
    with pytest.raises(VoiceUnavailableError):
        adapter.synthesize_speech("hello")


def test_transcribe_audio_with_unknown_placeholder_raises_voice_unavailable() -> None:
    adapter = LocalVoiceAdapter(stt_command="echo {unknown_placeholder}")
    with pytest.raises(VoiceUnavailableError):
        adapter.transcribe_audio(b"fake-audio", mime_type="audio/webm")
