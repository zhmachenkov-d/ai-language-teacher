"""FastAPI app factory for the loopback teacher HTTP API."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from teacher_service.adapters.api.auth import (
    AuthSettings,
    load_auth_token_from_env,
    tokens_match,
)

LOOPBACK_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

_UNAUTHORIZED_BODY = {
    "code": "unauthorized",
    "message": "Missing or invalid authentication token",
    "retryable": False,
}


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Reject every request without a valid Bearer token (including unmatched routes)."""

    def __init__(self, app: ASGIApp, *, token: str) -> None:
        super().__init__(app)
        self._token = token

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        presented = ""
        authorization = request.headers.get("Authorization", "")
        if authorization.lower().startswith("bearer "):
            presented = authorization[7:]
        if not tokens_match(presented, self._token):
            return JSONResponse(status_code=401, content=_UNAUTHORIZED_BODY)
        return await call_next(request)


def create_app(*, auth_token: str | None = None) -> FastAPI:
    """Build the API app. Token from arg (tests) or TEACHER_AUTH_TOKEN env."""
    token = auth_token if auth_token is not None else load_auth_token_from_env()
    settings = AuthSettings(token)
    app = FastAPI(
        title="teacher-service",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.auth = settings
    app.add_middleware(BearerAuthMiddleware, token=settings.token)

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

    return app
