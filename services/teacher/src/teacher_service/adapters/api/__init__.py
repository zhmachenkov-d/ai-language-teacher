"""HTTP API adapter: loopback FastAPI + Bearer local auth (Story 1.2)."""

from teacher_service.adapters.api.app import DEFAULT_PORT, LOOPBACK_HOST, create_app

__all__ = ["DEFAULT_PORT", "LOOPBACK_HOST", "create_app"]
