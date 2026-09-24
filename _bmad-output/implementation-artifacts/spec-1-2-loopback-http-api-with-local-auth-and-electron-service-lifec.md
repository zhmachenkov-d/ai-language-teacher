---
title: "1.2 Loopback HTTP API with local auth and Electron service lifecycle"
type: "feature"
created: "2026-09-24"
status: "done"
route: "dispatch"
review_loop_iteration: 0
baseline_commit: "a88e2ed356cbb90f6388c355d510ce55c9b4ac15"
context:
  - "{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md"
  - "{project-root}/_bmad-output/planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 1.1 left an installable teacher package with no listening HTTP API and no local auth, so nothing can safely call the service on loopback.

**Approach:** Add a FastAPI adapter that binds loopback-only, requires a Bearer local-auth token on every request, exposes `GET /health` with snake_case JSON and `{ code, message, retryable }` errors, plus a documented uvicorn entrypoint and pytest coverage.

**Done for this spec:** loopback API + Bearer auth + health + entrypoint + pytest (and AGENTS listen docs). **Not Done here:** Electron spawn/attach/preload, Vue health UI, tray/window-close host-survival, or polished status chrome — those remain open under `deferred-work.md` for this story key; marking this spec done does **not** close Epic Story 1.2 Electron/lifecycle ACs. Title keeps the sprint key; scope is API-auth only.

## Boundaries & Constraints

**Always:**

- Bind HTTP to `127.0.0.1` only (fixed port `8765`); reject missing/invalid `Authorization: Bearer <token>`
- Compare presented token to the configured secret with a constant-time (or equivalent non-early-exit) compare
- JSON `snake_case`; error bodies `{ code, message, retryable }` when returning JSON errors
- `/health` success and auth/error responses never echo the token, raw `Authorization` header, or `TEACHER_AUTH_TOKEN` env value
- Token supplied at process start via environment variable (e.g. `TEACHER_AUTH_TOKEN`) — never hardcoded or committed; tests mint ephemeral tokens
- Pin `uvicorn`; add a runnable package entrypoint (`uv run …`) that serves the app on loopback
- FastAPI allowed under `adapters/api/` only; keep domain forbidden-import isolation from 1.1
- Update AGENTS.md teacher Running section for listen + verify; note Electron lifecycle deferred
- Cover I/O matrix with pytest (TestClient) **and** a required listen+curl smoke in Verification

**Never:**

- Treat Electron spawn/attach/preload, Vue health UI, tray/window-close host-survival, or polished status chrome as Done criteria for this spec (see deferred-work.md)
- Config/SQLite (1.3), branded chrome/calendar/Settings (1.4–1.6), SSE, lesson/pedagogy APIs, Telegram, LLM/voice
- LAN bind (`0.0.0.0`); committed secrets; domain traffic over Electron IPC
- Edit vendor BMAD trees

## I/O & Edge-Case Matrix

| Scenario             | Input / State                       | Expected Output / Behavior                                          | Error Handling                |
| -------------------- | ----------------------------------- | ------------------------------------------------------------------- | ----------------------------- |
| Health with token    | App + valid Bearer on `GET /health` | `200` snake_case JSON status; body has no token/secret              | N/A                           |
| Health without token | Missing/invalid Authorization       | `401`/`403`; JSON `{ code, message, retryable }`; no token echo     | Reject without leaking secret |
| Non-loopback bind    | Host/CLI attempting LAN             | Entrypoint binds `127.0.0.1` only                                   | Fail closed if misconfigured  |
| Token mismatch       | Wrong Bearer vs process env token   | Rejected via constant-time compare; same error shape; no token echo | Auth failure                  |
| Domain isolation     | Existing domain AST tests           | Still pass; api adapter may import FastAPI                          | Fail if domain regresses      |

</frozen-after-approval>

## Code Map

- `_bmad-output/implementation-artifacts/epic-1-context.md` — AD-3/4/15 trust + wire rules
- `_bmad-output/planning-artifacts/epics.md` (Story 1.2) — API/auth ACs in-scope; Electron ACs deferred
- `_bmad-output/planning-artifacts/architecture/.../ARCHITECTURE-SPINE.md` — Bearer, loopback, `adapters/api`
- `_bmad-output/implementation-artifacts/spec-1-1-...md` — continuity; 1.1 banned FastAPI in adapters
- `_bmad-output/implementation-artifacts/deferred-work.md` — Electron lifecycle + host-survival + status chrome for this story
- `services/teacher/pyproject.toml` — pin uvicorn; `[project.scripts]` or equivalent entrypoint
- `services/teacher/src/teacher_service/adapters/api/` — app factory, Bearer dependency (constant-time compare), `GET /health`, CLI/`__main__`
- `services/teacher/tests/test_scaffold_imports.py` — allow FastAPI only under `adapters/api/`
- `services/teacher/tests/` — add auth/health/error-shape/no-leak tests (TestClient)
- `AGENTS.md` — teacher listen/verify; state Electron lifecycle deferred
- Do not change: `apps/desktop/**`, `domain/`, non-api adapters, vendor `_bmad/`

## Tasks & Acceptance

**Execution:**

- [x] `services/teacher/pyproject.toml` -- pin uvicorn; add runnable entrypoint -- listen path
- [x] `services/teacher/src/teacher_service/adapters/api/` -- FastAPI app, loopback bind, Bearer auth (constant-time compare), `GET /health`, error shape, no token echo -- AD-3/4/15
- [x] `services/teacher/tests/test_scaffold_imports.py` -- FastAPI only under `adapters/api/` -- 1.1 gate flip
- [x] `services/teacher/tests/` -- TestClient: token OK/deny, health JSON, error shape, no secret leak -- I/O matrix
- [x] Listen smoke -- documented entrypoint on `127.0.0.1:8765`; curl `/health` with Bearer → 200, without → reject -- required Verification
- [x] `AGENTS.md` -- document `uv run` listen + pytest; note Electron deferred -- honest runnability

**Acceptance Criteria:**

- Given the teacher package from 1.1, when the FastAPI adapter binds, then it listens on loopback only and every HTTP request without a valid local auth token is rejected (constant-time compare; responses never echo the token)
- Given a running teacher with a configured local token, when a client calls `GET /health` with the token, then the response succeeds with snake_case JSON and errors use `{ code, message, retryable }` when applicable
- Given `uv sync` and the documented listen entrypoint, when a developer follows AGENTS.md, then the service starts on `127.0.0.1:8765` with a token from the environment (not from the repo), and the required curl smoke passes
- Given this spec reaches Done, when sprint/story status is updated, then Electron spawn/preload, window-close host-survival, and polished status-chrome ACs from epics Story 1.2 remain open via deferred-work — they are not satisfied by this Done

## Implementation Notes

- 2026-09-24: Added `adapters/api` FastAPI factory (`create_app`), `hmac.compare_digest` Bearer auth via middleware (covers unmatched routes), `GET /health`, CLI `teacher-api` / `python -m teacher_service.adapters.api` binding only `127.0.0.1:8765`, uvicorn 0.53.0 + httpx (dev). Relaxed scaffold test to allow FastAPI under `adapters/api/` only. Review patches: whitespace token reject, fixed port only, openapi disabled, shaped 404s, CLI `uvicorn.run` mock assert. Verified: `uv run pytest` green; listen smoke Bearer→200, missing/wrong/openapi without token→401. Electron lifecycle remains deferred; sprint story stays in-progress until those ACs land.

## Spec Change Log

## Review Triage Log

- high — Auth only on `GET /health`; `/openapi.json` returns 200 without Bearer (verified with TestClient). Violates frozen “every request” / Bearer Always. → patch (global auth + disable openapi)
- high/medium (grouped with above) — Edge: unmatched routes and OpenAPI skip auth; same root cause as health-only Depends. → patch
- medium — Whitespace-only `TEACHER_AUTH_TOKEN` accepted (`"   "` truthy). Verified AuthSettings/`load_auth_token_from_env` only check emptiness, not strip. → patch
- medium — Frozen Always says fixed port `8765`; CLI accepts arbitrary `--port`. → patch (reject non-8765)
- medium — Verification-gap: CLI success path never asserts `uvicorn.run(..., host=127.0.0.1, port=8765)`; reject-only tests stay green if LAN bind sneaks in. → patch
- medium — Unhandled/`404` JSON may use FastAPI `{"detail":...}` not `{code,message,retryable}` (verified `/nope` 404). → patch (handlers)
- false — Matrix `401`/`403` with only `401` implemented: matrix allows either; no requirement both exist.
- false — Empty Spec Change Log / Triage at start of review: process timing; fix would only edit this build’s spec.
- false — Code Map `spec-1-1-...` ellipsis: documentation nit; fix edits this build’s spec.
- false — README omits curl smoke: AGENTS is the required runbook per tasks; README not an AC.
- false — `422` handler untested: matrix does not require a validation path; not an I/O row.
- low (rejected) — Align older deferred-work “spawn remains in-spec” evidence wording: editorial, not an end-user defect in this slice.
- defer — AGENTS unauthenticated smoke prints only HTTP code, not error body shape — fix edits agent-context `AGENTS.md`.
- defer — Epic remint/rotate-on-clear AC not explicitly parked in deferred-work beyond userData mint/load — track when Electron token bridge lands.

## Design Notes

- **Second split + party honesty patch:** Electron thin-host + preload + Vue smoke deferred; host-survival UX and status chrome also deferred. Done ≠ full epic Story 1.2 lifecycle.
- **Token via env:** Electron will later mint userData and pass the same env (deferred). Tests set env/ephemeral token for TestClient app factory.
- **Port `8765`:** Fixed for docs and later desktop attach.

## Verification

**Commands:**

- `cd services/teacher && uv sync && uv run pytest` -- expected: pass
- Listen smoke (required): start documented entrypoint with `TEACHER_AUTH_TOKEN` set, binding `127.0.0.1:8765`; `curl` `GET /health` with Bearer → `200` snake_case; same without Bearer (or wrong token) → reject with `{ code, message, retryable }` and no token in body -- expected: both sides pass

**Manual checks:**

- Electron GUI out of scope for this narrowed slice; do not treat desktop start as a Done gate here
