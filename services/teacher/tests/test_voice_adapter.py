"""Unit tests for production `LocalVoiceAdapter`.

Template-format errors plus happy-path synthesize/transcribe via stand-in
CLI commands (no espeak/whisper required) so fabricate-on-error cannot hide.
"""

from __future__ import annotations

import sys

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


def test_synthesize_speech_runs_command_and_returns_audio_bytes() -> None:
    # Stand-in TTS: copy the text file to the wav path (non-empty bytes).
    adapter = LocalVoiceAdapter(tts_command="cp {text_file} {out_file}")
    audio = adapter.synthesize_speech("hello-audio")
    assert audio == b"hello-audio"


def test_transcribe_audio_runs_command_and_returns_transcript() -> None:
    # Stand-in STT: write a transcript .txt into out_dir.
    py = sys.executable
    stt = (
        f"{py} -c \"open(r'{{out_dir}}/out.txt','w',encoding='utf-8')"
        f".write('said hello')\""
    )
    adapter = LocalVoiceAdapter(stt_command=stt)
    transcript = adapter.transcribe_audio(b"\x00\x01\x02", mime_type="audio/wav")
    assert transcript == "said hello"


def test_synthesize_speech_missing_engine_raises_voice_unavailable() -> None:
    adapter = LocalVoiceAdapter(
        tts_command="/nonexistent-teacher-tts-engine {text_file} {out_file}"
    )
    with pytest.raises(VoiceUnavailableError, match="not found"):
        adapter.synthesize_speech("hello")


def test_synthesize_speech_empty_output_raises_voice_unavailable() -> None:
    py = sys.executable
    tts = f"{py} -c \"open(r'{{out_file}}','wb').write(b'')\""
    adapter = LocalVoiceAdapter(tts_command=tts)
    with pytest.raises(VoiceUnavailableError, match="no audio"):
        adapter.synthesize_speech("hello")
