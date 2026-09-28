"""FastAPI app factory for the loopback teacher HTTP API."""

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from teacher_service.ports.config import ConfigPort

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


def create_app(
    *,
    auth_token: str | None = None,
    config: ConfigPort | None = None,
) -> FastAPI:
    """Build the API app. Token: arg → env → Config bearer (fail closed)."""
    if config is None:
        from teacher_service.adapters.config import FileConfig

        config = FileConfig()
    token = resolve_auth_token(auth_token, config=config)
    settings = AuthSettings(token)
    app = FastAPI(
        title="teacher-service",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.auth = settings
    app.state.config = config
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

    return app
