---
title: "1.1 Scaffold Electron+Vue desktop and Python teacher package"
type: "feature"
created: "2026-09-24"
status: "done"
route: "dispatch"
review_loop_iteration: 0
baseline_commit: "df13672a75dbb08845cee22e226dc7598447fde0"
context:
  - "{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md"
  - "{project-root}/_bmad-output/planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The repo has planning artifacts but no `apps/desktop/` or `services/teacher/` substrate, so teaching features have nowhere to land.

**Approach:** Create a pinned electron-vite Vue 3 desktop app under `apps/desktop/` and an installable hexagonal Python ≥3.12 package under `services/teacher/` (import name `teacher_service`), with documented install/verify commands and no secrets in git. Desktop must start without the teacher. Teacher in this story is installable + testable — not a listening HTTP service yet (Story 1.2).

## Boundaries & Constraints

**Always:**

- Desktop: hand-author a minimal electron-vite `vue-ts` tree under `apps/desktop/` with pinned Electron/Vue/Vite in `package.json` (do **not** invoke `npm create …@latest`). Layout must include Electron main, preload, and Vue 3 renderer sources plus electron-vite config
- Teacher: `services/teacher/` uv project; installable package name `teacher_service` at `src/teacher_service/{domain,ports,adapters/{api,persistence,llm,voice,telegram,config},graphs}/`
- Pins: Python ≥3.12 (pin patch), FastAPI ~0.141, LangGraph ~1.2 + langchain-core; declare `pytest` as a **dev** dependency
- Domain (`teacher_service.domain`) must not import forbidden modules (exact list in I/O matrix / test)
- Adapter stubs are empty `__init__.py` only — **no** FastAPI `app` object, no uvicorn entrypoint in 1.1
- Update AGENTS.md “Running and verifying” with exact install + verify commands (desktop: `npm install` / `npm run build` / documented start; teacher: `uv sync` / `uv run pytest`)
- Secrets: if any tool emits `.env`, leave untracked and add `.env.example` placeholders only; otherwise add no env files. Never commit real keys
- Partial-failure rule: if `apps/desktop/` or `services/teacher/` exists but is incomplete (missing required files below), delete the incomplete tree and recreate; if already complete and valid, skip recreate (idempotent)

**Never:**

- Use `npm create @quick-start/electron@latest` (or any unpinned `@latest` generator) for this story
- Implement loopback auth, Electron lifecycle attach, Config/SQLite app-data, branded chrome, calendar, or Settings (Stories 1.2–1.6)
- Wire domain traffic over Electron IPC; add monorepo orchestrators (nx/turbo)
- Edit vendor BMAD trees; rewrite planning contracts under `_bmad-output/` for this story
- Claim teacher “run” means an HTTP server in 1.1; commit `.env` with real keys

## I/O & Edge-Case Matrix

| Scenario                 | Input / State                                            | Expected Output / Behavior                                                                                                                                                                                                      | Error Handling                                                        |
| ------------------------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Desktop install + build  | Clean checkout; AGENTS desktop install + `npm run build` | Build succeeds; main/preload/renderer + pinned deps present                                                                                                                                                                     | npm errors surface; do not mark done                                  |
| Desktop start (display)  | Display available; AGENTS start command                  | Placeholder Electron window opens; no teacher required                                                                                                                                                                          | Record failure; do not skip manual gate when display exists           |
| Desktop start (headless) | No display / CI / this devcontainer                      | `npm run build` required; start command documented; optional `xvfb-run` smoke **if** xvfb installed — otherwise headless Done = build + docs only, and Implementation Notes must state window AC deferred to human-with-display | Do not treat build alone as having “seen” a window                    |
| Teacher install + test   | AGENTS teacher install                                   | `uv sync` succeeds; `uv run pytest` passes                                                                                                                                                                                      | Missing Python ≥3.12 fails via uv                                     |
| Domain isolation         | `tests/test_scaffold_imports.py`                         | `import teacher_service.domain`; domain tree imports none of: `electron`, `vue`, `fastapi`, `uvicorn`, `langgraph`, `langchain`, `langchain_core`, `openai`, `anthropic`, `telegram`, `aiogram`, `telebot`                      | Test fails on any hit                                                 |
| Secrets hygiene          | After scaffold                                           | No tracked `.env` with secrets; `.env.example` only if `.env` was emitted                                                                                                                                                       | Untrack `.env`                                                        |
| Partial scaffold retry   | Incomplete `apps/desktop/` or `services/teacher/`        | Remove incomplete tree; recreate full scaffold                                                                                                                                                                                  | Abort with clear error if unsure rather than nesting a second project |

</frozen-after-approval>

## Code Map

- `AGENTS.md` — replace Running TODO with exact commands; note scaffolded layout + pins; keep policy/conventions
- `.gitignore` — reuse; extend only for starter local-only artifacts
- `.devcontainer/` — reuse; do not redesign
- `_bmad-output/implementation-artifacts/epic-1-context.md` — epic constraints
- `_bmad-output/planning-artifacts/epics.md` (Story 1.1) — acceptance source (window start = human/display gate when GUI absent)
- `_bmad-output/planning-artifacts/architecture/.../ARCHITECTURE-SPINE.md` — Stack families + Structural Seed (folders under package `teacher_service`)
- `apps/desktop/package.json` — **create** pinned electron-vite + Electron + Vue 3 + Vite; scripts: `dev`/`build`/`preview` as appropriate
- `apps/desktop/` electron-vite config + `src/main`, `src/preload`, `src/renderer` (or starter-equivalent paths) — hand-authored minimal placeholder UI
- `services/teacher/pyproject.toml` — uv project, package `teacher_service`, runtime pins + `[dependency-groups] dev` / `dev-dependencies` including `pytest`
- `services/teacher/src/teacher_service/__init__.py` and stub `__init__.py` for `domain`, `ports`, `adapters/api|persistence|llm|voice|telegram|config`, `graphs` — empty stubs only
- `services/teacher/tests/test_scaffold_imports.py` — import + forbidden-module scan on `src/teacher_service/domain/`
- Do not change: `_bmad/` vendor, `.agents/skills/bmad-*/**`, planning contracts (consume only)

## Tasks & Acceptance

**Execution:**

- [x] `apps/desktop/` -- hand-author electron-vite vue-ts layout with pinned Electron/Vue/Vite; ensure main, preload, renderer; no `@latest` generator -- deterministic desktop substrate
- [x] Partial-failure -- if incomplete desktop/teacher tree exists, delete and recreate; if complete, skip -- idempotent scaffold
- [x] `apps/desktop/` -- `npm install` + `npm run build`; document start script; if display present, confirm placeholder window; if headless, note window gate in Implementation Notes -- AC + environment honesty
- [x] `services/teacher/pyproject.toml` -- package `teacher_service`; pin Python ≥3.12, FastAPI ~0.141, LangGraph ~1.2, langchain-core; add pytest as dev dep -- installable teacher substrate
- [x] `services/teacher/src/teacher_service/{domain,ports,adapters/*,graphs}/__init__.py` -- empty stubs only (no FastAPI app) -- hexagonal seed without 1.2 scope
- [x] `services/teacher/tests/test_scaffold_imports.py` -- `import teacher_service.domain` + forbidden-import list from I/O matrix -- required isolation gate
- [x] `AGENTS.md` -- exact install/build/start (desktop) and `uv sync` / `uv run pytest` (teacher); state teacher HTTP run is Story 1.2 -- honest runnability
- [x] Secrets hygiene -- untrack `.env` if emitted; `.env.example` only then; else no env files -- secrets policy

**Acceptance Criteria:**

- Given a clean checkout, when desktop is hand-scaffolded under `apps/desktop/` with pinned Electron/Vue/Vite, then main, preload, and Vue 3 renderer exist, `npm run build` succeeds, start is documented, and when a display is available the placeholder window opens without requiring the teacher (when headless, build + docs satisfy automation; window confirm remains a human gate recorded in Implementation Notes)
- Given the teacher scaffold, when `services/teacher/src/teacher_service/` includes domain/ports/adapters stubs/graphs and `pyproject.toml` pins FastAPI/LangGraph family plus pytest (dev), then `uv sync` and `uv run pytest` succeed, `import teacher_service.domain` works, and domain has none of the forbidden imports listed above
- Given scaffold complete, when a developer follows AGENTS.md, then both packages install cleanly, no secrets are committed, and incomplete partial trees were not left nested

## Implementation Notes

- 2026-09-24: Hand-authored `apps/desktop/` (electron-vite 5.0.0, Electron 44.4.5, Vue 3.5.43, Vite 7.3.6) and `services/teacher/` (`teacher_service`, Python 3.12.11, FastAPI 0.141.1, LangGraph 1.2.12, langchain-core 1.6.4). Verified: `npm install` + `npm run build` (desktop); `uv sync` + `uv run pytest` (5 passed). No `.env` emitted. Window AC deferred: this environment has `DISPLAY=:0` but Electron fails at runtime (`libatk-1.0.so.0` missing; no `xvfb-run`); placeholder window confirm awaits a machine with a working display + Electron system deps.

## Spec Change Log

## Review Triage Log

- false — Task `[x]` on desktop window while Notes defer: task text allows headless path (build + Notes); deferral matches approved Intent/Verification.
- false — `window-all-closed` → `app.quit()`: no teacher process in 1.1; quitting Electron does not violate AD-2 yet (Story 1.2 owns lifecycle).
- false — Empty Spec Change Log at start of review: expected until loopback; triage is being filled now.
- false — Spec `in-review` vs empty prior triage: process timing, not a code defect.
- low (rejected) — Electron `createWindow`/loadURL/`did-fail-load` guards: everyday scaffold unlikely; fix adds branches beyond a trivial correction.
- low (rejected) — `sandbox: false` unexplained: personal-desktop scaffold; hardening belongs with 1.2 thin-host lifecycle, not unexplained complexity now.
- low (rejected) — AST misses `importlib`/`__import__`: empty domain stubs; dynamic bypass not a demonstrated path.
- high/medium carried: none.
- medium — `sprint-status.yaml` `story_location` multiline parses as nested map, not a path string — break tooling that reads location. → patch
- medium — Story still `in-progress` in sprint-status while spec is `in-review` — status surfaces disagree. → patch (`review`)
- medium — Implementation Notes say pytest “2 passed” but suite has 4 tests — stale verification note. → patch
- medium — `epic-1-context.md` still shows flat `domain/` under `services/teacher/` — contradicts `src/teacher_service/` scaffold; later stories will misread layout. → patch
- medium — Domain AST ignores relative `ImportFrom` with `module is None` — isolation gate false-green if relative re-export of forbidden name. → patch
- medium — No test that adapter stubs stay free of FastAPI `app`/uvicorn (verification-gap, pre-verified). → patch
- medium — `.env` hygiene only under `services/teacher/` — desktop/root `.env` / `.env.local` evade check. → patch
- low — `test_hexagonal_stub_layout_complete` omits `adapters/__init__.py` though file exists in seed. → patch
- medium — `@types/node` not a direct desktop `devDependency` while `tsconfig.node.json` requests `"types": ["node"]` — fragile clean installs. → patch
- low — `vue-tsc` in package.json but no script; type errors need not fail verify. → patch (add `typecheck` script)
- defer — AGENTS.md omits Linux Electron system libs (`libatk`): fix edits AGENTS.md agent-context → defer
- defer — No automated proof desktop starts without teacher beyond `npm run build` (verification-gap disposition). → defer
- defer — Diff includes party-mode `.memlog.md` outside story Code Map — leave memory; do not treat as scaffold deliverable. → defer

## Design Notes

- **Why hand-author desktop:** party review found `create-electron@latest` non-deterministic (prompts, nesting, unpinned major). Known tree + pinned `package.json` beats generator lottery.
- **Package name `teacher_service`:** avoids generic PyPI/venv collision with `teacher`; folder remains `services/teacher/` per Structural Seed.
- **No FastAPI app in 1.1:** deps are pinned for later stories; listening server + auth = Story 1.2. AGENTS must not invent a fake `uvicorn` run.
- **Headless vs window AC:** epic wants a window; this environment may lack a display. Split verification explicitly so Done cannot mean “build passed, window imagined.”
- **Forbidden imports:** closed list in the test — no vague “vendor SDKs.”

## Verification

**Commands:**

- Desktop: `npm install` && `npm run build` in `apps/desktop/` -- expected: success
- Teacher: `uv sync` && `uv run pytest` in `services/teacher/` -- expected: pass
- Secrets: no tracked `.env` with real keys

**Manual checks:**

- With display: run documented desktop start; confirm placeholder window; no teacher required
- Headless: skip visual window; write one Implementation Notes line that window AC awaits a display machine
