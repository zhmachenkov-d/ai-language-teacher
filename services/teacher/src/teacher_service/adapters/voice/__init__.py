"""Voice adapter: local TTS/STT via configurable CLI engines (no cloud fallback).

v1 shells out to a local command-line engine (default `espeak-ng` for TTS;
a Whisper-CLI-shaped command for STT). Neither ships bundled with the app —
if the configured engine is missing or fails, this raises `VoiceUnavailableError`
so the API/UI can show a real retry/Settings path rather than a fake pass
(VOICE: REAL_STT / LISTENING_AUDIO: TTS). Packaging a bundled local engine
under `ConfigPort.voice_models_dir()` is tracked as follow-up (see report).
"""

from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path

from teacher_service.ports.voice import VoiceUnavailableError

TTS_COMMAND_ENV = "TEACHER_TTS_COMMAND"
STT_COMMAND_ENV = "TEACHER_STT_COMMAND"
# `{text_file}`/`{out_file}` and `{audio_file}`/`{out_dir}` are substituted via str.format.
DEFAULT_TTS_COMMAND = "espeak-ng -v en -f {text_file} -w {out_file}"
DEFAULT_STT_COMMAND = (
    "whisper {audio_file} --model base --language en "
    "--output_format txt --output_dir {out_dir}"
)
_TIMEOUT_SECONDS = 60


class LocalVoiceAdapter:
    """Shells out to a local TTS/STT engine. Missing/failing engine raises —
    never fakes a pass."""

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
                timeout=_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as exc:
            raise VoiceUnavailableError(f"local voice engine not found: {exc}") from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", "ignore")[:200] if exc.stderr else ""
            raise VoiceUnavailableError(f"local voice engine failed: {stderr}") from exc
        except subprocess.TimeoutExpired as exc:
            raise VoiceUnavailableError("local voice engine timed out") from exc
