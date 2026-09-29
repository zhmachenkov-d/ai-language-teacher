"""Unit tests for production Voice adapters: local CLI, cloud HTTP, composite.

Template-format errors plus happy-path synthesize/transcribe via stand-in
CLI commands (no espeak/whisper required). Cloud path uses mocked urllib —
no live vendor. Composite covers local-first / config-gated fallback matrix.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

import pytest
from teacher_service.adapters.config import SECRET_CLOUD_VOICE_API_KEY, FileConfig
from teacher_service.adapters.voice import (
    CLOUD_VOICE_BASE_URL_ENV,
    CloudVoiceAdapter,
    LocalThenCloudVoice,
    LocalVoiceAdapter,
)
from teacher_service.ports.voice import VoiceUnavailableError

# Minimal valid RIFF/WAVE header (12 bytes) + a few payload bytes.
_MIN_WAV = b"RIFF\x24\x00\x00\x00WAVE" + b"fmt " + b"\x00" * 8


@pytest.fixture
def config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FileConfig:
    root = tmp_path / "teacher-data"
    monkeypatch.setenv("TEACHER_DATA_DIR", str(root))
    cfg = FileConfig(root)
    cfg.ensure_layout()
    return cfg


class _FakeHttpResponse:
    def __init__(self, body: bytes, *, status: int = 200) -> None:
        self._body = body
        self.status = status

    def read(self) -> bytes:
        return self._body

    def getcode(self) -> int:
        return self.status

    def __enter__(self) -> _FakeHttpResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class _RecordingLocal:
    """Local VoicePort stand-in for composite tests."""

    def __init__(
        self,
        *,
        audio: bytes = _MIN_WAV,
        transcript: str = "local transcript",
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


class _RecordingCloud:
    """Cloud VoicePort stand-in — raises if called unexpectedly."""

    def __init__(
        self,
        *,
        audio: bytes = _MIN_WAV,
        transcript: str = "cloud transcript",
        synth_error: Exception | None = None,
        transcribe_error: Exception | None = None,
    ) -> None:
        self.audio = audio
        self.transcript = transcript
        self.synth_error = synth_error
        self.transcribe_error = transcribe_error
        self.synth_calls = 0
        self.transcribe_calls = 0
        self.last_text: str | None = None
        self.last_audio: bytes | None = None

    def synthesize_speech(self, text: str) -> bytes:
        self.synth_calls += 1
        self.last_text = text
        if self.synth_error is not None:
            raise self.synth_error
        return self.audio

    def transcribe_audio(self, audio_bytes: bytes, *, mime_type: str) -> str:
        self.transcribe_calls += 1
        self.last_audio = audio_bytes
        if self.transcribe_error is not None:
            raise self.transcribe_error
        return self.transcript


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


def test_cloud_tts_posts_json_and_returns_wav(
    config: FileConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-test-key")
    monkeypatch.setenv(CLOUD_VOICE_BASE_URL_ENV, "https://voice.test")
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeHttpResponse:
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["content_type"] = request.get_header("Content-type")
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _FakeHttpResponse(_MIN_WAV)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    adapter = CloudVoiceAdapter(config)
    audio = adapter.synthesize_speech("hello cloud")
    assert audio == _MIN_WAV
    assert captured["url"] == "https://voice.test/v1/tts"
    assert captured["authorization"] == "Bearer cv-test-key"
    assert captured["content_type"] == "application/json"
    assert captured["body"] == {"text": "hello cloud"}
    assert captured["timeout"] == 30


def test_cloud_stt_posts_audio_and_returns_transcript(
    config: FileConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-test-key")
    monkeypatch.setenv(CLOUD_VOICE_BASE_URL_ENV, "https://voice.test")
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeHttpResponse:
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["content_type"] = request.get_header("Content-type")
        captured["body"] = request.data
        return _FakeHttpResponse(json.dumps({"transcript": " said hello "}).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    adapter = CloudVoiceAdapter(config)
    transcript = adapter.transcribe_audio(b"\x00\x01", mime_type="audio/webm")
    assert transcript == "said hello"
    assert captured["url"] == "https://voice.test/v1/stt"
    assert captured["authorization"] == "Bearer cv-test-key"
    assert captured["content_type"] == "audio/webm"
    assert captured["body"] == b"\x00\x01"


def test_cloud_tts_non_wav_raises(config: FileConfig, monkeypatch: pytest.MonkeyPatch) -> None:
    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-test-key")

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeHttpResponse:
        return _FakeHttpResponse(b"not-a-wav")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(VoiceUnavailableError, match="non-WAV"):
        CloudVoiceAdapter(config).synthesize_speech("hello")


def test_cloud_stt_empty_transcript_raises(
    config: FileConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-test-key")

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeHttpResponse:
        return _FakeHttpResponse(json.dumps({"transcript": "  "}).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(VoiceUnavailableError, match="empty transcript"):
        CloudVoiceAdapter(config).transcribe_audio(b"x", mime_type="audio/wav")


@pytest.mark.parametrize(
    "body",
    [
        b"not-json",
        json.dumps({"other": "field"}).encode(),
        b"\xff\xfe\x00",  # non-UTF-8
    ],
)
def test_cloud_stt_unparseable_response_raises(
    config: FileConfig, monkeypatch: pytest.MonkeyPatch, body: bytes
) -> None:
    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-test-key")

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeHttpResponse:
        return _FakeHttpResponse(body)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(VoiceUnavailableError, match="unparseable"):
        CloudVoiceAdapter(config).transcribe_audio(b"x", mime_type="audio/wav")


def test_cloud_http_error_maps_to_voice_unavailable(
    config: FileConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-test-key")

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeHttpResponse:
        raise HTTPError(request.full_url, 401, "Unauthorized", hdrs=None, fp=None)  # type: ignore[arg-type]

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(VoiceUnavailableError, match="HTTP 401"):
        CloudVoiceAdapter(config).synthesize_speech("hello")


def test_cloud_transport_error_maps_to_voice_unavailable(
    config: FileConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-test-key")

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeHttpResponse:
        raise URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(VoiceUnavailableError, match="request failed"):
        CloudVoiceAdapter(config).synthesize_speech("hello")


def test_cloud_missing_secret_raises(config: FileConfig) -> None:
    with pytest.raises(VoiceUnavailableError, match="not configured"):
        CloudVoiceAdapter(config).synthesize_speech("hello")


def test_composite_local_ok_cloud_unset_skips_cloud(config: FileConfig) -> None:
    local = _RecordingLocal()
    cloud = _RecordingCloud()
    composite = LocalThenCloudVoice(local, cloud, config)
    assert composite.synthesize_speech("hi") == _MIN_WAV
    assert local.synth_calls == 1
    assert cloud.synth_calls == 0


def test_composite_local_ok_cloud_keyed_skips_cloud(config: FileConfig) -> None:
    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-present")
    local = _RecordingLocal()
    cloud = _RecordingCloud()
    composite = LocalThenCloudVoice(local, cloud, config)
    assert composite.synthesize_speech("hi") == _MIN_WAV
    assert composite.transcribe_audio(b"a", mime_type="audio/wav") == "local transcript"
    assert local.synth_calls == 1
    assert local.transcribe_calls == 1
    assert cloud.synth_calls == 0
    assert cloud.transcribe_calls == 0


def test_composite_local_fail_cloud_unset_raises_no_cloud(config: FileConfig) -> None:
    local = _RecordingLocal(synth_error=VoiceUnavailableError("espeak missing"))
    cloud = _RecordingCloud()
    composite = LocalThenCloudVoice(local, cloud, config)
    with pytest.raises(VoiceUnavailableError, match="espeak missing"):
        composite.synthesize_speech("hi")
    assert cloud.synth_calls == 0


def test_composite_local_fail_cloud_keyed_uses_cloud(config: FileConfig) -> None:
    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-present")
    local = _RecordingLocal(
        synth_error=VoiceUnavailableError("espeak missing"),
        transcribe_error=VoiceUnavailableError("whisper missing"),
    )
    cloud = _RecordingCloud(audio=_MIN_WAV, transcript="from cloud")
    composite = LocalThenCloudVoice(local, cloud, config)
    assert composite.synthesize_speech("hi") == _MIN_WAV
    assert cloud.last_text == "hi"
    assert composite.transcribe_audio(b"mic", mime_type="audio/webm") == "from cloud"
    assert cloud.last_audio == b"mic"
    assert local.synth_calls == 1
    assert cloud.synth_calls == 1
    assert local.transcribe_calls == 1
    assert cloud.transcribe_calls == 1


def test_composite_both_fail_raises_voice_unavailable(config: FileConfig) -> None:
    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-present")
    local = _RecordingLocal(synth_error=VoiceUnavailableError("local fail"))
    cloud = _RecordingCloud(synth_error=VoiceUnavailableError("cloud fail"))
    composite = LocalThenCloudVoice(local, cloud, config)
    with pytest.raises(VoiceUnavailableError, match="cloud fail"):
        composite.synthesize_speech("hi")


def test_composite_whitespace_secret_treated_as_unset(config: FileConfig) -> None:
    # FileConfig strips; writing whitespace-only is rejected. Simulate unset
    # after local fail: no secret file → no cloud call.
    local = _RecordingLocal(synth_error=VoiceUnavailableError("local fail"))
    cloud = _RecordingCloud()
    composite = LocalThenCloudVoice(local, cloud, config)
    with pytest.raises(VoiceUnavailableError, match="local fail"):
        composite.synthesize_speech("hi")
    assert cloud.synth_calls == 0


class _FakeConfigWhitespaceSecret:
    """Config that returns whitespace for the cloud key (FileConfig would strip)."""

    def get_secret(self, name: str) -> str | None:
        if name == SECRET_CLOUD_VOICE_API_KEY:
            return "  "
        return None


def test_composite_whitespace_secret_from_config_skips_cloud() -> None:
    local = _RecordingLocal(synth_error=VoiceUnavailableError("local fail"))
    cloud = _RecordingCloud()
    composite = LocalThenCloudVoice(local, cloud, _FakeConfigWhitespaceSecret())  # type: ignore[arg-type]
    with pytest.raises(VoiceUnavailableError, match="local fail"):
        composite.synthesize_speech("hi")
    assert cloud.synth_calls == 0


def test_composite_non_unavailable_local_error_does_not_fall_through(
    config: FileConfig,
) -> None:
    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-present")
    local = _RecordingLocal(synth_error=RuntimeError("unexpected bug"))
    cloud = _RecordingCloud()
    composite = LocalThenCloudVoice(local, cloud, config)
    with pytest.raises(RuntimeError, match="unexpected bug"):
        composite.synthesize_speech("hi")
    assert cloud.synth_calls == 0


def test_composite_re_reads_secret_per_call(config: FileConfig) -> None:
    local = _RecordingLocal(synth_error=VoiceUnavailableError("local fail"))
    cloud = _RecordingCloud()
    composite = LocalThenCloudVoice(local, cloud, config)

    with pytest.raises(VoiceUnavailableError):
        composite.synthesize_speech("first")
    assert cloud.synth_calls == 0

    config.set_secret(SECRET_CLOUD_VOICE_API_KEY, "cv-later")
    assert composite.synthesize_speech("second") == _MIN_WAV
    assert cloud.synth_calls == 1
