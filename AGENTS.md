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
npm run dev          # start (dev): placeholder Electron window; teacher not required
# or after build:
npm run preview      # start (preview production build)
```

### Teacher (`services/teacher/`)

Installable + testable in Story 1.1. A listening HTTP server is Story 1.2 — do not treat `uv run` as starting an API.

```bash
cd services/teacher
uv sync
uv run pytest
```

## Conventions that differ from defaults

- Put pedagogy and scheduling only in `services/teacher/src/teacher_service/domain/`; domain must not import Vue, Electron, Telegram SDK, or vendor LLM/voice SDKs — use ports.
- Keep Electron main a thin host (window + teacher lifecycle only); domain traffic is loopback HTTP (+ SSE for live lessons), not Electron IPC as a domain bus.
- Living plan and Progress writes go through teacher domain use cases only; UI and Telegram issue commands — they must not write plan/Progress rows or treat UI cache as source of truth.
- LangGraph owns in-phase agent loops only; it must persist via domain use cases, never SQLite directly.
- Wire JSON is `snake_case` everywhere (HTTP and SSE), including from the Vue client.

<!-- /bmad:context -->
