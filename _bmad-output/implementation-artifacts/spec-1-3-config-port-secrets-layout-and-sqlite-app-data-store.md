---
title: "1.3 Config port, secrets layout, and SQLite app-data store"
type: "feature"
created: "2026-09-27"
status: "done"
route: "dispatch"
review_loop_iteration: 0
baseline_commit: "ef76c801fff12c730dce6ccdae4c351ce5ab071d"
context:
  - "{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md"
  - "{project-root}/_bmad-output/planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After 1.2 the teacher has loopback auth + `/health`, but no Config port, OS app-data layout, secrets store, or SQLite — keys and learner prefs have nowhere durable to live.

**Approach:** Ship Config + `adapters/config` for one OS app-data layout (secrets including Bearer token, SQLite, reserved voice-cache dir), persistence that creates/loads a minimal Learner, and pytest proving the ports. No new HTTP projection and no desktop work in this slice.

**Decisions:**

- Bearer local-auth token is stored/loaded under app-data via Config; `TEACHER_AUTH_TOKEN` remains bootstrap/override for first run and tests. Resolve order for the live token: `create_app(auth_token=...)` when not `None` → non-empty stripped env → Config secret → else fail closed (CLI exit 1). Empty/whitespace env counts as unset (fall through).
- Authenticated HTTP learner/profile (or config-status) projection is deferred — see `deferred-work.md` for this source_spec.
- Layout + Learner get-or-create are proven in pytest via ports. CLI listen must resolve Config/data-dir for Bearer only — SQLite/Learner init is not required to start `/health`.

## Boundaries & Constraints

**Always:**

- Config resolves one learner data directory under OS app-data; SQLite, secrets, and a reserved voice-model cache subdirectory share that layout (same logical layout for dev/installed; overrideable for tests via `TEACHER_DATA_DIR`)
- Persist LLM and placeholder Telegram secrets only via Config with single-user OS file permissions; never hardcoded/committed; never logged or returned as free-text identity (NFR1 — held by Config-only access; no LLM adapter in this slice)
- Also persist/load the Bearer API token via Config under the secrets layout; existing `/health` + middleware keep working with the resolved token (order in Decisions)
- SQLite sole durable store; on first init create/load Learner with opaque UUID `id` plus `target_language`, `L1`, `timezone` (v1 defaults `en` / `ru` / `UTC`)
- Domain owns Learner get-or-create via ports; `adapters/config` and `adapters/persistence` implement; keep domain isolation tests green
- Update AGENTS.md for data-dir override, Config/SQLite pytest notes, and Bearer-via-Config (env override) listen notes

**Never:**

- New authenticated HTTP learner/profile or config-status projection (deferred); HTTP write/mutate for secrets/prefs (Settings 1.6)
- Electron spawn/attach/preload, window-close host-survival, Vue Settings, desktop SQLite/secrets duplication
- Requiring SQLite/Learner init as a precondition for CLI listen / `/health`
- Living plan, Progress, lessons, SSE, Telegram bot, LLM/voice adapter bodies beyond Config placeholders
- LAN bind; committed secrets; vendor `_bmad/` edits

## I/O & Edge-Case Matrix

| Scenario          | Input / State                                           | Expected Output / Behavior                                                               | Error Handling                             |
| ----------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------ |
| Fresh data dir    | Empty override dir; Config + persistence init (pytest)  | Layout created (db + secrets dir + voice-cache); Learner defaults `en`/`ru`/`UTC` + UUID | Fail closed if dir not creatable           |
| Bearer via Config | No env token; Config has bearer secret                  | CLI/`create_app` auth uses Config token; `/health` 200 with Bearer                       | Fail if neither arg, env, nor Config token |
| Env override      | Non-empty `TEACHER_AUTH_TOKEN` + different Config token | Env wins (after explicit `auth_token` arg)                                               | Whitespace-only env = unset                |
| Explicit arg      | `create_app(auth_token="…")` with env/Config also set   | Arg wins (tests)                                                                         | N/A                                        |
| Secret persist    | Set LLM (optional Telegram) via Config port             | Readable only via Config get; single-user mode; never in logs                            | Never log raw values                       |
| Secret absent     | No LLM secret yet                                       | Config reports missing; Learner still loadable                                           | No crash                                   |
| Test override     | `TEACHER_DATA_DIR` → temp path                          | All files under override                                                                 | Pytest isolation                           |

</frozen-after-approval>

## Code Map

- `_bmad-output/implementation-artifacts/epic-1-context.md` — AD-4/7/18; Learner fields
- `_bmad-output/planning-artifacts/epics.md` (Story 1.3) — AC source; API projection deferred
- `_bmad-output/planning-artifacts/architecture/.../ARCHITECTURE-SPINE.md` — AD-4, AD-7, AD-10, AD-18
- `_bmad-output/implementation-artifacts/spec-1-2-...md` — Bearer middleware, `create_app(auth_token=…)`, `/health`
- `_bmad-output/implementation-artifacts/deferred-work.md` — HTTP projection + Electron lifecycle
- `services/teacher/src/teacher_service/ports/config.py` — Protocol: data-dir paths + secret get/set
- `services/teacher/src/teacher_service/ports/persistence.py` — Protocol: Learner create/load
- `services/teacher/src/teacher_service/adapters/config/` — app-data resolve, layout, secret files
- `services/teacher/src/teacher_service/adapters/persistence/` — SQLite Learner create/load
- `services/teacher/src/teacher_service/domain/learner.py` — Learner model + get-or-create via ports
- `services/teacher/src/teacher_service/adapters/api/auth.py` — `resolve_auth_token(...)` (arg → env → Config)
- `services/teacher/src/teacher_service/adapters/api/{app,cli}.py` — call resolver; keep `/health`; CLI no SQLite require
- `services/teacher/pyproject.toml` — pin `platformdirs` (or equivalent) if used
- `services/teacher/tests/test_config_persistence.py` (or split) — temp-dir I/O matrix; isolation stays green
- `AGENTS.md` — data dir + Bearer-via-Config listen notes
- Do not change: `apps/desktop/**`, vendor `_bmad/`

## Tasks & Acceptance

**Execution:**

- [x] `services/teacher/src/teacher_service/ports/config.py` -- Protocol for data-dir paths + secret get/set -- AD-1
- [x] `services/teacher/src/teacher_service/ports/persistence.py` -- Protocol for Learner create/load -- AD-1
- [x] `services/teacher/src/teacher_service/adapters/config/` -- resolve data dir; create layout; get/set named secrets with 0600 -- AD-4/AD-18
- [x] `services/teacher/src/teacher_service/adapters/persistence/` -- SQLite init + Learner create/load (UUID, en/ru/UTC) -- AD-7/AD-10
- [x] `services/teacher/src/teacher_service/domain/learner.py` -- Learner model + get-or-create use case via ports -- hexagonal
- [x] `services/teacher/src/teacher_service/adapters/api/auth.py` -- `resolve_auth_token(arg, env, config)` per Decisions order -- Decision B
- [x] `services/teacher/src/teacher_service/adapters/api/{app,cli}.py` -- wire resolver into `create_app`/CLI; `/health` unchanged; CLI no SQLite require -- 1.2 continuity
- [x] `services/teacher/pyproject.toml` -- pin `platformdirs` (or chosen helper) -- scaffold pin
- [x] `services/teacher/tests/` -- temp-dir tests for layout/secrets/Learner/token resolve matrix -- I/O matrix
- [x] `AGENTS.md` -- Running notes for data dir + Bearer-via-Config -- honest runnability

**Acceptance Criteria:**

- Given the teacher from 1.2, when Config resolves the learner data directory (pytest with override), then SQLite, secrets, and a reserved voice-cache path share one OS app-data layout
- Given LLM/Telegram secrets and the Bearer token written/loaded through Config, when auth resolves (arg → env → Config), then `/health` accepts the resolved Bearer and secret values never appear in logs or health JSON
- Given no prior store, when persistence initializes, then a Learner with opaque UUID id and defaults `target_language=en`, `L1=ru`, `timezone=UTC` can be created and loaded
- Given CLI listen, when only Config/env Bearer is available, then `/health` starts without requiring SQLite/Learner init
- Given this slice reaches Done, when sprint status is updated, then the HTTP learner/profile projection AC from epics Story 1.3 remains open via deferred-work — not satisfied by this Done

## Implementation Notes

- Implemented ConfigPort + FileConfig (`platformdirs==4.12.0`, `TEACHER_DATA_DIR` override): layout `teacher.sqlite`, `secrets/{bearer_token,llm_api_key,telegram_bot_token}` (0600), `voice-models/`.
- PersistencePort + SqliteStore (stdlib sqlite3); domain `Learner` + `get_or_create_learner` with defaults en/ru/UTC.
- `resolve_auth_token`: arg (if not None) → non-empty stripped env → Config `bearer_token` → ValueError; whitespace env = unset. CLI ensure_layout for Bearer only; no Learner init required for listen.
- Tests: `test_config_persistence.py` covers I/O matrix; existing auth tests updated for Config fall-through + data-dir isolation. `uv run pytest` → 30 passed.
- HTTP learner/profile projection remains deferred (`deferred-work.md`).

## Spec Change Log

## Review Triage Log

- false — Blind: new-file hunks at repo-root `src/teacher_service/...` — disproved: package lives under `services/teacher/`; artifact of how untracked diffs were staged, not misplaced code
- false — Blind: implementation spec absent from diff so contract unverifiable — disproved: `spec-1-3-...md` exists on disk (untracked); review uses the live claims file path
- false — Blind: sprint status stuck at `in-progress` not `review` — disproved: workflow sets sprint `review` at present; spec frontmatter already `in-review`
- defer — Blind: AGENTS documents Config bearer listen but no operable bootstrap without Settings — real; fix edits AGENTS.md agent-context → defer
- medium — Blind/VG: I/O “dir not creatable” / layout RuntimeError → CLI exit 1 untested — verified: `ensure_layout` raises RuntimeError; CLI catches it; no test — route patch
- medium — Blind: second `create_learner` / single-learner enforcement untested — verified: raise path exists, no test — route patch
- low — Blind: dir mode `0700` never asserted — verified chmod in ensure_layout; add assertion — route patch
- false — Blind: `get_secret` never re-applies 0600 on leftover world-readable files — not everyday single-user threat; `set_secret` always chmods; no demonstrated bad outcome in v1 path
- medium — Blind: `resolve_auth_token` hardcodes `"bearer_token"` vs `SECRET_BEARER_TOKEN` — verified at auth.py:64 — route patch
- low — Blind: APP_AUTHOR == APP_NAME nests on Windows platformdirs — Linux path identical; set author None for cleaner cross-platform — route patch
- medium — VG: default `platformdirs` data-dir identity never asserted — carried as filed — route patch
- low — Blind/Edge: concurrent get_or_create / dual INSERT race — real in theory; v1 single-process desktop unlikely everyday; reject (complexity > everyday harm)
- medium — Edge: UTF-8 decode on secret read not wrapped — verified: only OSError caught at layout.py:90-93 — route patch
- medium — Edge: chmod fails after write_text leaves umask-permission secret — verified write-then-chmod order — route patch
- medium — Edge: secret path symlink can escape secrets_dir — verified path join without resolve check — route patch
- medium — Edge: multiple learner rows silently return LIMIT 1 — verified load_learner — route patch
- low — Edge: raw sqlite3 errors propagate — soft; reject (unlikely everyday; wrapping adds noise)
- false — Edge claim: Windows secrets never get 0600 — disproved: Design Notes/tests intentionally skip `nt`; ACL model differs
- medium — VG: `create_app()` Config-bearer success without `config=` untested — carried as filed — route patch
- medium — VG other: CLI host/port/bind tests omit `TEACHER_DATA_DIR` and write real OS app-data — verified test_api_auth_health.py:123-163 — route patch

## Design Notes

- Prefer stdlib `sqlite3`; resolve OS app-data via pinned `platformdirs` + `TEACHER_DATA_DIR` override.
- Layout: `teacher.sqlite`, `secrets/bearer_token`, `secrets/llm_api_key`, `secrets/telegram_bot_token` (0600), `voice-models/` empty dir.
- Token resolve: `auth_token` arg if not `None` → non-empty stripped `TEACHER_AUTH_TOKEN` → Config `bearer_token` → else fail closed (CLI exit 1). Whitespace-only env = unset.
- CLI listen: Config for Bearer only; layout/Learner proven in pytest — do not block listen on SQLite.
- NFR1 LLM-context: no LLM adapter in this slice; secrets reachable only via Config port.
- No new HTTP routes; projection stays deferred.

## Verification

**Commands:**

- `cd services/teacher && uv sync && uv run pytest` -- expected: all green including Config/SQLite/Bearer-resolve tests
- Listen smoke: documented start with Config-stored or env Bearer; `GET /health` with Bearer → 200; without → 401 -- expected: AGENTS.md updated
