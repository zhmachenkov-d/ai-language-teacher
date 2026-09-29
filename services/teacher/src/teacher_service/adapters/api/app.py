"""FastAPI app factory for the loopback teacher HTTP API."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Callable
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from teacher_service.adapters.api.auth import (
    AuthSettings,
    resolve_auth_token,
    tokens_match,
)
from teacher_service.adapters.config import SECRET_LLM_API_KEY
from teacher_service.adapters.persistence import SqliteStore
from teacher_service.domain.learner import (
    ALLOWED_LESSON_DURATIONS,
    INTAKE_STEPS,
    LearnerValidationError,
    WeeklySlot,
    get_or_create_learner,
    update_learner,
)
from teacher_service.domain.living_plan import (
    LivingPlanError,
    create_living_plan,
    get_living_plan,
    living_plan_to_wire,
)
from teacher_service.domain.placement import (
    PLACEMENT_STAGES,
    PlacementItemsError,
    parse_placement_items,
    placement_items_public,
    placement_items_to_storage,
    score_speaking_transcript,
)
from teacher_service.ports.llm import LlmGenerationError
from teacher_service.ports.voice import VoiceUnavailableError

if TYPE_CHECKING:
    from teacher_service.ports.config import ConfigPort
    from teacher_service.ports.llm import LlmPort
    from teacher_service.ports.persistence import PersistencePort
    from teacher_service.ports.voice import VoicePort

LOOPBACK_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

_UNAUTHORIZED_BODY = {
    "code": "unauthorized",
    "message": "Missing or invalid authentication token",
    "retryable": False,
}

# Vue renderer origins that may call loopback HTTP (Vite/Electron http(s) + file:// → null).
_LOOPBACK_ORIGIN_REGEX = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
_CORS_ALLOW_ORIGINS = ["null"]
_CORS_ALLOW_METHODS = ["GET", "PUT", "POST", "PATCH", "DELETE", "OPTIONS"]
_CORS_ALLOW_HEADERS = ["Authorization", "Content-Type"]


class LlmConfigUpdate(BaseModel):
    """PUT /config/llm body — a non-empty LLM API key (never echoed back)."""

    llm_api_key: str

    @field_validator("llm_api_key")
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("llm_api_key must be a non-empty string")
        return value


class WeeklySlotIn(BaseModel):
    weekday: int
    start_minute: int

    @field_validator("weekday")
    @classmethod
    def _weekday_range(cls, value: int) -> int:
        if not (0 <= value <= 6):
            raise ValueError("weekday must be 0–6")
        return value

    @field_validator("start_minute")
    @classmethod
    def _start_minute_range(cls, value: int) -> int:
        if not (0 <= value <= 1439):
            raise ValueError("start_minute must be 0–1439")
        return value


# ~4 MB of base64 text (~3 MB decoded) — covers a few short mic prompts with
# headroom, rejects runaway uploads before base64 decode + STT.
_MAX_SPEAKING_AUDIO_BASE64_CHARS = 4_000_000


class SpeakingAudioIn(BaseModel):
    """POST /placement/speaking/transcribe body — base64 local mic capture."""

    audio_base64: str
    mime_type: str = "audio/webm"

    @field_validator("audio_base64")
    @classmethod
    def _audio_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("audio_base64 must be a non-empty string")
        if len(value) > _MAX_SPEAKING_AUDIO_BASE64_CHARS:
            raise ValueError("audio_base64 exceeds the maximum allowed size")
        return value


class LivingPlanCreateBody(BaseModel):
    """POST /living-plan body — must be exactly `{}` (POST_BODY)."""

    model_config = ConfigDict(extra="forbid")


class LearnerPatch(BaseModel):
    """PATCH /learner — all fields optional; omitted keys are unchanged."""

    address_as: str | None = None
    age: int | None = None
    goals: list[str] | None = None
    desired_outcome: list[str] | None = None
    interests: list[str] | None = None
    emphasis: list[str] | None = None
    lesson_duration_minutes: int | None = None
    timezone: str | None = None
    weekly_slots: list[WeeklySlotIn] | None = None
    intake_step: str | None = None
    consent_mic: bool | None = None
    consent_telegram: bool | None = None
    consent_ai: bool | None = None
    consent_privacy: bool | None = None
    consent_complete: bool | None = None
    placement_stage: str | None = None
    placement_written_answers: list[int] | None = None
    placement_listening_played: bool | None = None
    placement_listening_answers: list[int] | None = None
    placement_complete: bool | None = None

    @field_validator("address_as")
    @classmethod
    def _address_as_nonblank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("address_as must be a non-empty string")
        return value

    @field_validator("age")
    @classmethod
    def _age_range(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if not (1 <= value <= 120):
            raise ValueError("age must be 1–120")
        return value

    @field_validator("lesson_duration_minutes")
    @classmethod
    def _duration_allowed(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value not in ALLOWED_LESSON_DURATIONS:
            raise ValueError("lesson_duration_minutes must be 30, 45, or 60")
        return value

    @field_validator("timezone")
    @classmethod
    def _timezone_nonblank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("timezone must be a non-empty string")
        return value

    @field_validator("intake_step")
    @classmethod
    def _intake_step_allowed(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in INTAKE_STEPS:
            raise ValueError("invalid intake_step")
        return value

    @field_validator("placement_stage")
    @classmethod
    def _placement_stage_allowed(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in PLACEMENT_STAGES:
            raise ValueError("invalid placement_stage")
        return value

    @field_validator("placement_written_answers", "placement_listening_answers")
    @classmethod
    def _answers_are_ints(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in value):
            raise ValueError("answers must be a list of integers")
        return value


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Reject every request without a valid Bearer token (including unmatched routes)."""

    def __init__(self, app: ASGIApp, *, token: str) -> None:
        super().__init__(app)
        self._token = token

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # CORS preflight must reach CORSMiddleware without a Bearer requirement.
        if request.method == "OPTIONS":
            return await call_next(request)
        presented = ""
        authorization = request.headers.get("Authorization", "")
        if authorization.lower().startswith("bearer "):
            presented = authorization[7:]
        if not tokens_match(presented, self._token):
            return JSONResponse(status_code=401, content=_UNAUTHORIZED_BODY)
        return await call_next(request)


def _placement_items_public_or_none(
    raw_items: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Client-safe items projection — never leak `correct_index` over the wire."""
    if raw_items is None:
        return None
    try:
        return placement_items_public(parse_placement_items(raw_items))
    except PlacementItemsError:
        # Corrupt persisted payload — surface as absent rather than leaking raw shape.
        return None


def _learner_to_dict(learner: Any) -> dict[str, Any]:
    return {
        "id": learner.id,
        "target_language": learner.target_language,
        "l1": learner.l1,
        "timezone": learner.timezone,
        "address_as": learner.address_as,
        "age": learner.age,
        "goals": list(learner.goals),
        "desired_outcome": list(learner.desired_outcome),
        "interests": list(learner.interests),
        "emphasis": list(learner.emphasis),
        "lesson_duration_minutes": learner.lesson_duration_minutes,
        "weekly_slots": [
            {"weekday": s.weekday, "start_minute": s.start_minute}
            for s in learner.weekly_slots
        ],
        "intake_step": learner.intake_step,
        "consent_mic": learner.consent_mic,
        "consent_telegram": learner.consent_telegram,
        "consent_ai": learner.consent_ai,
        "consent_privacy": learner.consent_privacy,
        "consent_complete": learner.consent_complete,
        "placement_stage": learner.placement_stage,
        "placement_items": _placement_items_public_or_none(learner.placement_items),
        "placement_written_answers": list(learner.placement_written_answers),
        "placement_written_score": learner.placement_written_score,
        "placement_listening_generated": learner.placement_listening_generated,
        "placement_listening_played": learner.placement_listening_played,
        "placement_listening_answers": list(learner.placement_listening_answers),
        "placement_listening_score": learner.placement_listening_score,
        "placement_speaking_transcript": learner.placement_speaking_transcript,
        "placement_speaking_score": learner.placement_speaking_score,
        "placement_complete": learner.placement_complete,
        "plan_complete": learner.plan_complete,
    }


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


def create_app(
    *,
    auth_token: str | None = None,
    config: ConfigPort | None = None,
    store: PersistencePort | None = None,
    llm: LlmPort | None = None,
    voice: VoicePort | None = None,
    now_provider: Callable[[], datetime] | None = None,
) -> FastAPI:
    """Build the API app. Token: arg → env → Config bearer (fail closed)."""
    if config is None:
        from teacher_service.adapters.config import FileConfig

        config = FileConfig()
    token = resolve_auth_token(auth_token, config=config)
    settings = AuthSettings(token)
    if store is None:
        store = SqliteStore(config.sqlite_path())
    if llm is None:
        from teacher_service.adapters.llm import OpenAiLlmAdapter

        llm = OpenAiLlmAdapter(config)
    if voice is None:
        from teacher_service.adapters.voice import LocalVoiceAdapter

        voice = LocalVoiceAdapter()
    app = FastAPI(
        title="teacher-service",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.auth = settings
    app.state.config = config
    app.state.store = store
    app.state.llm = llm
    app.state.voice = voice
    app.state.now_provider = now_provider or _default_now
    # Middleware order: last added runs first. CORS must wrap Bearer so preflight
    # is answered before auth; Bearer still skips OPTIONS defensively.
    app.add_middleware(BearerAuthMiddleware, token=settings.token)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_CORS_ALLOW_ORIGINS,
        allow_origin_regex=_LOOPBACK_ORIGIN_REGEX,
        allow_credentials=False,
        allow_methods=_CORS_ALLOW_METHODS,
        allow_headers=_CORS_ALLOW_HEADERS,
    )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if (
            isinstance(detail, dict)
            and "code" in detail
            and "message" in detail
            and "retryable" in detail
        ):
            body = {
                "code": detail["code"],
                "message": detail["message"],
                "retryable": detail["retryable"],
            }
        else:
            body = {
                "code": "http_error",
                "message": str(detail),
                "retryable": False,
            }
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "validation_error",
                "message": "Request validation failed",
                "retryable": False,
            },
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/config/llm")
    async def get_llm_config(request: Request) -> dict[str, bool]:
        cfg: ConfigPort = request.app.state.config
        try:
            configured = cfg.get_secret(SECRET_LLM_API_KEY) is not None
        except RuntimeError as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "config_error",
                    "message": str(exc),
                    "retryable": True,
                },
            ) from exc
        return {"configured": configured}

    @app.put("/config/llm")
    async def put_llm_config(
        payload: LlmConfigUpdate, request: Request
    ) -> dict[str, bool]:
        cfg: ConfigPort = request.app.state.config
        try:
            cfg.set_secret(SECRET_LLM_API_KEY, payload.llm_api_key)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "config_error",
                    "message": str(exc),
                    "retryable": True,
                },
            ) from exc
        return {"configured": True}

    @app.get("/learner")
    async def get_learner(request: Request) -> dict[str, Any]:
        persistence: PersistencePort = request.app.state.store
        learner = get_or_create_learner(persistence)
        return _learner_to_dict(learner)

    @app.patch("/learner")
    async def patch_learner(payload: LearnerPatch, request: Request) -> dict[str, Any]:
        persistence: PersistencePort = request.app.state.store
        raw = payload.model_dump(exclude_unset=True)
        kwargs: dict[str, Any] = {}
        for key, value in raw.items():
            if key == "weekly_slots" and value is not None:
                kwargs[key] = [
                    WeeklySlot(weekday=s["weekday"], start_minute=s["start_minute"])
                    for s in value
                ]
            else:
                kwargs[key] = value
        try:
            learner = update_learner(persistence, **kwargs)
        except LearnerValidationError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": exc.code,
                    "message": str(exc),
                    "retryable": False,
                },
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "validation_error",
                    "message": str(exc),
                    "retryable": False,
                },
            ) from exc
        return _learner_to_dict(learner)

    @app.post("/placement/items")
    async def generate_placement_items_endpoint(request: Request) -> dict[str, Any]:
        persistence: PersistencePort = request.app.state.store
        learner = get_or_create_learner(persistence)
        if not learner.consent_complete:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "placement_requires_consent",
                    "message": "placement requires consent_complete",
                    "retryable": False,
                },
            )
        # CONTENT: LLM_GEN — one LLM-generated item set per placement run.
        if learner.placement_items is not None:
            try:
                cached = parse_placement_items(learner.placement_items)
            except PlacementItemsError as exc:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "code": "placement_items_corrupt",
                        "message": str(exc),
                        "retryable": True,
                    },
                ) from exc
            return placement_items_public(cached)

        cfg: ConfigPort = request.app.state.config
        try:
            configured = cfg.get_secret(SECRET_LLM_API_KEY) is not None
        except RuntimeError as exc:
            raise HTTPException(
                status_code=500,
                detail={"code": "config_error", "message": str(exc), "retryable": True},
            ) from exc
        if not configured:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "llm_config_missing",
                    "message": "LLM API key is not configured",
                    "retryable": True,
                },
            )

        llm_port: LlmPort = request.app.state.llm
        try:
            raw = llm_port.generate_placement_items(
                target_language=learner.target_language,
                l1=learner.l1,
                interests=learner.interests,
                emphasis=learner.emphasis,
            )
        except LlmGenerationError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "llm_generation_failed",
                    "message": str(exc),
                    "retryable": True,
                },
            ) from exc
        try:
            items = parse_placement_items(raw)
        except PlacementItemsError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "llm_generation_failed",
                    "message": str(exc),
                    "retryable": True,
                },
            ) from exc

        update_learner(persistence, placement_items=placement_items_to_storage(items))
        return placement_items_public(items)

    @app.post("/placement/listening/audio")
    async def synthesize_listening_audio_endpoint(request: Request) -> dict[str, Any]:
        persistence: PersistencePort = request.app.state.store
        learner = get_or_create_learner(persistence)
        if not learner.consent_complete:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "placement_requires_consent",
                    "message": "placement requires consent_complete",
                    "retryable": False,
                },
            )
        if learner.placement_items is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "placement_items_missing",
                    "message": "generate placement items before requesting audio",
                    "retryable": True,
                },
            )
        try:
            items = parse_placement_items(learner.placement_items)
        except PlacementItemsError as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "placement_items_corrupt",
                    "message": str(exc),
                    "retryable": True,
                },
            ) from exc

        voice_port: VoicePort = request.app.state.voice
        try:
            audio = voice_port.synthesize_speech(items.listening.script)
        except VoiceUnavailableError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "voice_unavailable",
                    "message": str(exc),
                    "retryable": True,
                },
            ) from exc

        update_learner(persistence, placement_listening_generated=True)
        return {
            "audio_base64": base64.b64encode(audio).decode("ascii"),
            "mime_type": "audio/wav",
        }

    @app.post("/placement/speaking/transcribe")
    async def transcribe_speaking_audio_endpoint(
        payload: SpeakingAudioIn, request: Request
    ) -> dict[str, Any]:
        persistence: PersistencePort = request.app.state.store
        learner = get_or_create_learner(persistence)
        if not learner.consent_complete:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "placement_requires_consent",
                    "message": "placement requires consent_complete",
                    "retryable": False,
                },
            )
        if learner.placement_items is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "placement_items_missing",
                    "message": "generate placement items before speaking",
                    "retryable": True,
                },
            )
        try:
            items = parse_placement_items(learner.placement_items)
        except PlacementItemsError as exc:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "placement_items_corrupt",
                    "message": str(exc),
                    "retryable": True,
                },
            ) from exc

        try:
            audio_bytes = base64.b64decode(payload.audio_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "validation_error",
                    "message": str(exc),
                    "retryable": False,
                },
            ) from exc

        voice_port: VoicePort = request.app.state.voice
        try:
            transcript = voice_port.transcribe_audio(
                audio_bytes, mime_type=payload.mime_type
            )
        except VoiceUnavailableError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "voice_unavailable",
                    "message": str(exc),
                    "retryable": True,
                },
            ) from exc

        score = score_speaking_transcript(transcript, items.speaking_prompts)
        updated = update_learner(
            persistence,
            placement_speaking_transcript=transcript,
            placement_speaking_score=score,
        )
        return _learner_to_dict(updated)

    def _living_plan_http_error(exc: LivingPlanError) -> HTTPException:
        if exc.code == "living_plan_not_found":
            status = 404
        elif exc.code == "plan_inconsistent":
            status = 500
        else:
            status = 422
        return HTTPException(
            status_code=status,
            detail={
                "code": exc.code,
                "message": str(exc),
                "retryable": exc.retryable,
            },
        )

    @app.post("/living-plan")
    async def post_living_plan(
        payload: LivingPlanCreateBody, request: Request
    ) -> dict[str, Any]:
        # POST_BODY: only `{}` accepted (extra fields → 422 via extra=forbid).
        del payload  # empty body; presence validates shape
        persistence: PersistencePort = request.app.state.store
        llm_port: LlmPort = request.app.state.llm
        cfg: ConfigPort = request.app.state.config
        now_fn: Callable[[], datetime] = request.app.state.now_provider

        def _llm_configured(c: ConfigPort) -> bool:
            try:
                return c.get_secret(SECRET_LLM_API_KEY) is not None
            except RuntimeError as exc:
                raise LivingPlanError(
                    "llm_config_missing",
                    str(exc),
                    retryable=True,
                ) from exc

        try:
            projection = create_living_plan(
                persistence,
                llm_port,
                cfg,
                now=now_fn(),
                llm_configured=_llm_configured,
            )
        except LivingPlanError as exc:
            raise _living_plan_http_error(exc) from exc
        return living_plan_to_wire(projection)

    @app.get("/living-plan")
    async def get_living_plan_endpoint(request: Request) -> dict[str, Any]:
        persistence: PersistencePort = request.app.state.store
        learner = get_or_create_learner(persistence)
        try:
            projection = get_living_plan(persistence, learner)
        except LivingPlanError as exc:
            raise _living_plan_http_error(exc) from exc
        return living_plan_to_wire(projection)

    return app
