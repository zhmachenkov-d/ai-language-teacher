<!-- bmad:context -->
<!-- Verified 2026-09-23 against 442b13208d078e138cfb324c19057ccd8c2c74a4. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## ai-language-teacher

Personal desktop AI English teacher (v1): Electron + Vue UI client, Python teacher service (FastAPI, LangGraph, SQLite), hexagonal core. Canonical what-to-build: `_bmad-output/specs/spec-ai-language-teacher/SPEC.md` and its companions. How-to-build: `_bmad-output/planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md`. UX: `_bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/DESIGN.md` and `EXPERIENCE.md`.

## Policy

- Never push or commit directly to `main`; open a PR.
- Never send surname, postal/physical address, email, or phone into LLM-bound context — strip, redact, or do not collect.
- Never commit secrets (`.env`, API keys, Telegram tokens); store them via the Config port / local secrets layout from the architecture spine.
- Cursor always-on rules (Conventional Commits; do not edit vendor BMAD — customize via `_bmad/custom/`): `.cursor/rules/`. Do not duplicate those rules here.

## Where things are

- Product contract: `_bmad-output/specs/spec-ai-language-teacher/` (`SPEC.md`, `glossary.md`, `lesson-templates.md`, `stories.yaml`)
- Architecture decisions: `_bmad-output/planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md`
- UX spines: `_bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/`
- Layout: `apps/desktop/` (electron-vite main + preload + Vue 3 renderer; pinned Electron 44.4.5 / Vue 3.5.43 / Vite 7.3.6 / electron-vite 5.0.0); `services/teacher/` installable package `teacher_service` under `src/teacher_service/` (`domain/`, `ports/`, `adapters/{api,persistence,llm,voice,telegram,config}/`, `graphs/`); Python 3.12.11 floor, FastAPI 0.141.1, LangGraph 1.2.12, langchain-core 1.6.4

## Running and verifying

### Desktop (`apps/desktop/`)

```bash
cd apps/desktop
npm install
npm run build
npm run dev          # start (dev): Electron window + tray host; teacher spawn/attach on ready
# or after build:
npm run preview      # start (preview production build)
```

### Teacher (`services/teacher/`)

Loopback HTTP API with Bearer local auth (Story 1.2) plus Config/SQLite under OS app-data (Story 1.3). Electron main spawn/attach/preload and window-close host-survival (tray-first) shipped in Story 1.6 — desktop start **is** the normal teacher listen path via `TeacherHost`. Authenticated HTTP learner/profile projection remains deferred (only `/health` and `/config/llm` in Epic 1). Renderer→teacher HTTP needs CSP `connect-src` for `:8765` and CORS on the API (loopback Origin / `null` for `file://`).

Data directory: OS app-data via `platformdirs` (`ai-language-teacher`), containing `teacher.sqlite`, `secrets/` (`bearer_token`, `llm_api_key`, `telegram_bot_token`), and `voice-models/`. Override for tests/dev with `TEACHER_DATA_DIR`. Host and CLI share the same layout (host may set `TEACHER_DATA_DIR` when spawning).

Bearer resolve order for listen/`create_app`: explicit `auth_token` arg (when not `None`) → non-empty stripped `TEACHER_AUTH_TOKEN` → Config `bearer_token` secret → fail closed (CLI exit 1). Whitespace-only env counts as unset. Electron mints/loads Config `bearer_token` and passes it to the child via env on spawn. CLI listen resolves Config for Bearer only — SQLite/Learner init is not required to start `/health`. Prove layout + Learner get-or-create with `uv run pytest` (temp `TEACHER_DATA_DIR`).

```bash
cd services/teacher
uv sync
uv run pytest

# Listen on 127.0.0.1:8765 — token from env (bootstrap/override) or Config bearer_token:
export TEACHER_AUTH_TOKEN="$(openssl rand -hex 32)"
# optional: export TEACHER_DATA_DIR=/tmp/teacher-data-dev
uv run teacher-api
# or: uv run python -m teacher_service.adapters.api

# Smoke:
curl -sS -H "Authorization: Bearer $TEACHER_AUTH_TOKEN" http://127.0.0.1:8765/health
# expect 200 snake_case JSON, e.g. {"status":"ok"}
curl -sS http://127.0.0.1:8765/health
# expect 401 with {"code","message","retryable"}
```

Desktop verify (after `npm install` in `apps/desktop/`): `npm test` (Vitest) and `npm run build`.

## Conventions that differ from defaults

- Put pedagogy and scheduling only in `services/teacher/src/teacher_service/domain/`; domain must not import Vue, Electron, Telegram SDK, or vendor LLM/voice SDKs — use ports.
- Keep Electron main a thin host (window + teacher lifecycle only); domain traffic is loopback HTTP (+ SSE for live lessons), not Electron IPC as a domain bus.
- Living plan and Progress writes go through teacher domain use cases only; UI and Telegram issue commands — they must not write plan/Progress rows or treat UI cache as source of truth.
- LangGraph owns in-phase agent loops only; it must persist via domain use cases, never SQLite directly.
- Wire JSON is `snake_case` everywhere (HTTP and SSE), including from the Vue client.

<!-- /bmad:context -->

## Dev Container GUI (Electron)

This environment includes `desktop-lite` (noVNC). After rebuild: open forwarded port **6080** (password `vscode`), then `cd apps/desktop && npm run dev`. `ELECTRON_DISABLE_SANDBOX=1` is set via `containerEnv`. Headless smoke without VNC: `npm run preview:xvfb`.
