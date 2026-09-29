"""Voice adapters: local CLI engines + optional config-gated cloud HTTP fallback.

`LocalVoiceAdapter` stays Config-free. `CloudVoiceAdapter` implements the Cloud
HTTP contract (stdlib urllib). `LocalThenCloudVoice` owns the Config gate:
try local first; on `VoiceUnavailableError` only, if `cloud_voice_api_key` is
non-empty on that call, retry cloud. Cloud never runs silently (AD-9).
"""

from __future__ import annotations

import http.client
import json
import os
import shlex
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

from teacher_service.adapters.config import SECRET_CLOUD_VOICE_API_KEY
from teacher_service.ports.voice import VoiceUnavailableError

if TYPE_CHECKING:
    from teacher_service.ports.config import ConfigPort
    from teacher_service.ports.voice import VoicePort

TTS_COMMAND_ENV = "TEACHER_TTS_COMMAND"
STT_COMMAND_ENV = "TEACHER_STT_COMMAND"
# `{text_file}`/`{out_file}` and `{audio_file}`/`{out_dir}` are substituted via str.format.
DEFAULT_TTS_COMMAND = "espeak-ng -v en -f {text_file} -w {out_file}"
DEFAULT_STT_COMMAND = (
    "whisper {audio_file} --model base --language en "
    "--output_format txt --output_dir {out_dir}"
)
_LOCAL_TIMEOUT_SECONDS = 60

CLOUD_VOICE_BASE_URL_ENV = "TEACHER_CLOUD_VOICE_BASE_URL"
# Unreachable stub host for docs when env unset; tests inject mocked urlopen.
DEFAULT_CLOUD_VOICE_BASE_URL = "http://127.0.0.1:9"
_CLOUD_TIMEOUT_SECONDS = 30


def _is_wav_bytes(data: bytes) -> bool:
    """True when `data` looks like a RIFF/WAVE container (non-empty WAV)."""
    return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE"


class LocalVoiceAdapter:
    """Shells out to a local TTS/STT engine. Missing/failing engine raises —
    never fakes a pass. Config-free."""

    def __init__(
        self,
        *,
        tts_command: str | None = None,
        stt_command: str | None = None,
    ) -> None:
        self._tts_command = tts_command or os.environ.get(
            TTS_COMMAND_ENV, DEFAULT_TTS_COMMAND
        )
        self._stt_command = stt_command or os.environ.get(
            STT_COMMAND_ENV, DEFAULT_STT_COMMAND
        )

    def synthesize_speech(self, text: str) -> bytes:
        with tempfile.TemporaryDirectory() as tmp:
            text_file = Path(tmp) / "script.txt"
            out_file = Path(tmp) / "speech.wav"
            text_file.write_text(text, encoding="utf-8")
            command = self._format_command(
                self._tts_command, text_file=text_file, out_file=out_file
            )
            self._run(command)
            if not out_file.is_file() or out_file.stat().st_size == 0:
                raise VoiceUnavailableError("local TTS engine produced no audio")
            return out_file.read_bytes()

    def transcribe_audio(self, audio_bytes: bytes, *, mime_type: str) -> str:
        suffix = ".wav" if "wav" in mime_type else ".webm"
        with tempfile.TemporaryDirectory() as tmp:
            audio_file = Path(tmp) / f"capture{suffix}"
            audio_file.write_bytes(audio_bytes)
            out_dir = Path(tmp)
            command = self._format_command(
                self._stt_command, audio_file=audio_file, out_dir=out_dir
            )
            self._run(command)
            txt_files = sorted(out_dir.glob("*.txt"))
            if not txt_files:
                raise VoiceUnavailableError("local STT engine produced no transcript")
            transcript = txt_files[0].read_text(encoding="utf-8").strip()
            if not transcript:
                raise VoiceUnavailableError("local STT engine returned an empty transcript")
            return transcript

    @staticmethod
    def _format_command(template: str, **kwargs: Path) -> str:
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError, IndexError) as exc:
            raise VoiceUnavailableError(
                f"invalid voice command template: {exc}"
            ) from exc

    @staticmethod
    def _run(command: str) -> None:
        try:
            subprocess.run(
                shlex.split(command),
                check=True,
                capture_output=True,
                timeout=_LOCAL_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as exc:
            raise VoiceUnavailableError(f"local voice engine not found: {exc}") from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", "ignore")[:200] if exc.stderr else ""
            raise VoiceUnavailableError(f"local voice engine failed: {stderr}") from exc
        except subprocess.TimeoutExpired as exc:
            raise VoiceUnavailableError("local voice engine timed out") from exc


class CloudVoiceAdapter:
    """Cloud HTTP contract for TTS/STT. Re-reads `cloud_voice_api_key` per call;
    maps transport/empty/auth failures to `VoiceUnavailableError` only."""

    def __init__(
        self,
        config: ConfigPort,
        *,
        base_url: str | None = None,
    ) -> None:
        self._config = config
        self._base_url_override = base_url

    def synthesize_speech(self, text: str) -> bytes:
        api_key = self._api_key()
        base = self._base_url()
        body = json.dumps({"text": text}).encode("utf-8")
        request = urllib.request.Request(
            f"{base}/v1/tts",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        raw = self._open(request)
        if not raw or not _is_wav_bytes(raw):
            raise VoiceUnavailableError("cloud TTS returned empty or non-WAV audio")
        return raw

    def transcribe_audio(self, audio_bytes: bytes, *, mime_type: str) -> str:
        api_key = self._api_key()
        base = self._base_url()
        request = urllib.request.Request(
            f"{base}/v1/stt",
            data=audio_bytes,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": mime_type,
            },
        )
        raw = self._open(request)
        try:
            payload = json.loads(raw)
            transcript = payload["transcript"]
        except (KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise VoiceUnavailableError(
                f"cloud STT returned an unparseable response: {exc}"
            ) from exc
        if not isinstance(transcript, str) or not transcript.strip():
            raise VoiceUnavailableError("cloud STT returned an empty transcript")
        return transcript.strip()

    def _api_key(self) -> str:
        try:
            api_key = self._config.get_secret(SECRET_CLOUD_VOICE_API_KEY)
        except RuntimeError as exc:
            raise VoiceUnavailableError(
                f"cloud voice API key unavailable: {exc}"
            ) from exc
        if not api_key:
            raise VoiceUnavailableError("cloud voice API key is not configured")
        return api_key

    def _base_url(self) -> str:
        if self._base_url_override is not None:
            raw = self._base_url_override
        else:
            raw = os.environ.get(
                CLOUD_VOICE_BASE_URL_ENV, DEFAULT_CLOUD_VOICE_BASE_URL
            )
        cleaned = (raw or "").strip().rstrip("/")
        if not cleaned:
            cleaned = DEFAULT_CLOUD_VOICE_BASE_URL.rstrip("/")
        return cleaned

    @staticmethod
    def _open(request: urllib.request.Request) -> bytes:
        try:
            with urllib.request.urlopen(
                request, timeout=_CLOUD_TIMEOUT_SECONDS
            ) as response:
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()
                if status != 200:
                    raise VoiceUnavailableError(
                        f"cloud voice request failed with HTTP {status}"
                    )
                return response.read()
        except VoiceUnavailableError:
            raise
        except urllib.error.HTTPError as exc:
            raise VoiceUnavailableError(
                f"cloud voice request failed with HTTP {exc.code}"
            ) from exc
        except (
            urllib.error.URLError,
            OSError,
            TimeoutError,
            http.client.HTTPException,
        ) as exc:
            raise VoiceUnavailableError(f"cloud voice request failed: {exc}") from exc


class LocalThenCloudVoice:
    """Composite VoicePort: local first; cloud only after `VoiceUnavailableError`
    when the cloud secret is present on that call. Other local exceptions do not
    fall through to cloud."""

    def __init__(
        self,
        local: VoicePort,
        cloud: VoicePort,
        config: ConfigPort,
    ) -> None:
        self._local = local
        self._cloud = cloud
        self._config = config

    def synthesize_speech(self, text: str) -> bytes:
        try:
            return self._local.synthesize_speech(text)
        except VoiceUnavailableError:
            if not self._cloud_keyed():
                raise
            return self._cloud.synthesize_speech(text)

    def transcribe_audio(self, audio_bytes: bytes, *, mime_type: str) -> str:
        try:
            return self._local.transcribe_audio(audio_bytes, mime_type=mime_type)
        except VoiceUnavailableError:
            if not self._cloud_keyed():
                raise
            return self._cloud.transcribe_audio(audio_bytes, mime_type=mime_type)

    def _cloud_keyed(self) -> bool:
        try:
            secret = self._config.get_secret(SECRET_CLOUD_VOICE_API_KEY)
        except RuntimeError as exc:
            raise VoiceUnavailableError(
                f"cloud voice API key unavailable: {exc}"
            ) from exc
        return bool(secret and secret.strip())


__all__ = [
    "CLOUD_VOICE_BASE_URL_ENV",
    "DEFAULT_CLOUD_VOICE_BASE_URL",
    "DEFAULT_STT_COMMAND",
    "DEFAULT_TTS_COMMAND",
    "STT_COMMAND_ENV",
    "TTS_COMMAND_ENV",
    "CloudVoiceAdapter",
    "LocalThenCloudVoice",
    "LocalVoiceAdapter",
]
