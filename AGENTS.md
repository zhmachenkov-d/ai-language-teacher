<!-- bmad:context -->
<!-- Verified 2026-10-04 against 7d9779bda82465c18cb4f6499a607ba1f7245279. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## ai-language-teacher

Personal desktop AI English teacher (v1): Electron + Vue UI client, Python teacher service (FastAPI, LangGraph, SQLite), hexagonal core. Canonical what-to-build: `_bmad-output/initiative-ai-language-teacher/spec-ai-language-teacher/` (`spec-ai-language-teacher.md` and companions). How-to-build: `_bmad-output/initiative-ai-language-teacher/architecture-ai-language-teacher/architecture-ai-language-teacher.md`. UX: `_bmad-output/initiative-ai-language-teacher/ux-ai-language-teacher/DESIGN.md` and `EXPERIENCE.md`.

## Policy

- Never push or commit directly to `main`; open a PR.
- Never send surname, postal/physical address, email, or phone into LLM-bound context — strip, redact, or do not collect.
- Never commit secrets (`.env`, API keys, Telegram tokens); store them via the Config port / local secrets layout from the architecture spine.
- Cursor always-on rules (Conventional Commits; do not edit vendor BMAD — customize via `_bmad/custom/`): `.cursor/rules/`. Do not duplicate those rules here.

## Where things are

- Product contract: `_bmad-output/initiative-ai-language-teacher/spec-ai-language-teacher/` (`spec-ai-language-teacher.md`, `glossary.md`, `lesson-templates.md`, `stories.yaml`)
- Architecture decisions: `_bmad-output/initiative-ai-language-teacher/architecture-ai-language-teacher/architecture-ai-language-teacher.md`
- UX spines: `_bmad-output/initiative-ai-language-teacher/ux-ai-language-teacher/`
- Tickets/epics: `_bmad-output/initiative-ai-language-teacher/` (epic folders under the initiative)
- Layout: `apps/desktop/` (electron-vite main + preload + Vue 3 renderer; pinned Electron 44.4.5 / Vue 3.5.43 / Vite 7.3.6 / electron-vite 5.0.0); `services/teacher/` installable package `teacher_service` under `src/teacher_service/` (`domain/`, `ports/`, `adapters/{api,persistence,llm,voice,telegram,config}/`, `graphs/`); Python 3.12.11 floor, FastAPI 0.141.1, LangGraph 1.2.12, langchain-core 1.6.4

## Running and verifying

### Desktop (`apps/desktop/`)

```bash
cd apps/desktop
npm install
npm run build
npm run dev # start (dev): Electron window + tray host; teacher spawn/attach on ready
# or after build:
npm run preview # start (preview production build)
```

### Teacher (`services/teacher/`)

Loopback HTTP API with Bearer local auth plus Config/SQLite under OS app-data. Electron main spawn/attach/preload and window-close host-survival (tray-first) — desktop start **is** the normal teacher listen path via `TeacherHost`. Authenticated surfaces today: `/health`, `/config/llm`, `/config/voice` (cloud Voice key status only — not Settings mic prefs), `/learner`, `/placement/*`, `/living-plan`. Renderer→teacher HTTP needs CSP `connect-src` for `:8765` and CORS on the API (loopback Origin / `null` for `file://`).

Data directory: OS app-data via `platformdirs` (`ai-language-teacher`), containing `teacher.sqlite`, `secrets/` (`bearer_token`, `llm_api_key`, `telegram_bot_token`, `cloud_voice_api_key`), and `voice-models/`. Override for tests/dev with `TEACHER_DATA_DIR`. Host and CLI share the same layout (host may set `TEACHER_DATA_DIR` when spawning). Optional cloud Voice fallback (AD-9) is local-then-cloud behind VoicePort: set Config `cloud_voice_api_key` via `PUT /config/voice` (or `FileConfig.set_secret`) **and** `TEACHER_CLOUD_VOICE_BASE_URL` to a contract-compatible host — unset/default stub fails closed immediately (no silent cloud, no ~30s hang).

Bearer resolve order for listen/`create_app`: explicit `auth_token` arg (when not `None`) → non-empty stripped `TEACHER_AUTH_TOKEN` → Config `bearer_token` secret → fail closed (CLI exit 1). Whitespace-only env counts as unset. Electron mints/loads Config `bearer_token` and passes it to the child via env on spawn. CLI listen resolves Config for Bearer only — SQLite/Learner init is not required to start `/health`. Prove layout + Learner get-or-create with `uv run pytest` (temp `TEACHER_DATA_DIR`).

```bash
cd services/teacher
uv sync
uv run pytest

# optional: export TEACHER_DATA_DIR=/tmp/teacher-data-dev

# Bearer for listen — pick one:
# (A) env bootstrap/override:
export TEACHER_AUTH_TOKEN="$(openssl rand -hex 32)"
# (B) Config secret under app-data (no Settings UI / no env):
# TEACHER_DATA_DIR=/tmp/teacher-data-dev uv run python -c \
# "from teacher_service.adapters.config import FileConfig, SECRET_BEARER_TOKEN; \
# import secrets; c=FileConfig(); c.ensure_layout(); \
# c.set_secret(SECRET_BEARER_TOKEN, secrets.token_hex(32)); \
# print(c.get_secret(SECRET_BEARER_TOKEN))"
# then unset TEACHER_AUTH_TOKEN so CLI reads Config bearer_token

uv run teacher-api
# or: uv run python -m teacher_service.adapters.api

# Smoke:
curl -sS -H "Authorization: Bearer $TEACHER_AUTH_TOKEN" http://127.0.0.1:8765/health
# expect 200 snake_case JSON, e.g. {"status":"ok"}
curl -sS http://127.0.0.1:8765/health | tee /tmp/teacher-health-401.json
# expect 401; body must be {"code","message","retryable"} (jq installed in this image):
# jq -e 'keys|sort==["code","message","retryable"]' /tmp/teacher-health-401.json

# Optional cloud Voice key (never echoed; blank → 422):
# curl -sS -H "Authorization: Bearer $TEACHER_AUTH_TOKEN" \
# -H "Content-Type: application/json" \
# -d '{"cloud_voice_api_key":"…"}' http://127.0.0.1:8765/config/voice
# curl -sS -H "Authorization: Bearer $TEACHER_AUTH_TOKEN" http://127.0.0.1:8765/config/voice
# expect {"configured":true}
# export TEACHER_CLOUD_VOICE_BASE_URL=https://your-contract-host # required for cloud path
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

### Linux Electron system libraries

Bare Linux hosts (and older images) need Chromium/Electron runtime libs before `npm run dev` / `preview` can open a window. Common missing shared object: `libatk-1.0.so.0` (`libatk1.0-0`). This repo’s `.devcontainer/Dockerfile` installs the usual set (`libnss3`, `libatk-bridge2.0-0`, `libgtk-3-0`, `libgbm1`, `libasound2`, `xvfb`, …). Outside the devcontainer, install an equivalent Electron/Chromium dependency pack for your distro, or use `npm run preview:xvfb` when only headless smoke is needed.
