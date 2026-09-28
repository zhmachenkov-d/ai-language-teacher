"""FastAPI app factory for the loopback teacher HTTP API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
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
    WeeklySlot,
    get_or_create_learner,
    update_learner,
)

if TYPE_CHECKING:
    from teacher_service.ports.config import ConfigPort
    from teacher_service.ports.persistence import PersistencePort

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
    }


def create_app(
    *,
    auth_token: str | None = None,
    config: ConfigPort | None = None,
    store: PersistencePort | None = None,
) -> FastAPI:
    """Build the API app. Token: arg → env → Config bearer (fail closed)."""
    if config is None:
        from teacher_service.adapters.config import FileConfig

        config = FileConfig()
    token = resolve_auth_token(auth_token, config=config)
    settings = AuthSettings(token)
    if store is None:
        store = SqliteStore(config.sqlite_path())
    app = FastAPI(
        title="teacher-service",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.auth = settings
    app.state.config = config
    app.state.store = store
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
    async def patch_learner(
        payload: LearnerPatch, request: Request
    ) -> dict[str, Any]:
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

    return app
