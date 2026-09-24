"""CLI entrypoint: serve the teacher API on loopback only."""

from __future__ import annotations

import argparse
import sys

import uvicorn

from teacher_service.adapters.api.app import DEFAULT_PORT, LOOPBACK_HOST, create_app
from teacher_service.adapters.api.auth import load_auth_token_from_env


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Serve the teacher HTTP API on loopback (127.0.0.1 only)."
    )
    parser.add_argument(
        "--host",
        default=LOOPBACK_HOST,
        help=f"Bind host (must be {LOOPBACK_HOST}; LAN binds are rejected)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Bind port (default {DEFAULT_PORT})",
    )
    args = parser.parse_args(argv)

    if args.host != LOOPBACK_HOST:
        print(
            f"Refusing to bind host {args.host!r}; only {LOOPBACK_HOST} is allowed.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    if args.port != DEFAULT_PORT:
        print(
            f"Refusing to bind port {args.port}; only {DEFAULT_PORT} is allowed.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    try:
        load_auth_token_from_env()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    app = create_app()
    uvicorn.run(app, host=LOOPBACK_HOST, port=DEFAULT_PORT, log_level="info")


if __name__ == "__main__":
    main()
