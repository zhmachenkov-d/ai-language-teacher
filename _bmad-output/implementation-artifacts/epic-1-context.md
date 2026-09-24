# Epic 1 Context: Desktop teacher foundation

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Ship the runnable personal-desktop substrate: Electron+Vue UI and a background Python teacher service on loopback HTTP, with Config/secrets/SQLite under OS app-data, branded Russian chrome, an empty Outlook-like calendar home, and documented Settings shells (LLM/API save-ready; Voice/Telegram/Schedule/Goals placeholders). Closing the window must not stop the teacher process so later reminder/micro-lesson delivery can run. No product FRs land here — this epic enables all later work.

## Stories

- Story 1.1: Scaffold Electron+Vue desktop and Python teacher package
- Story 1.2: Loopback HTTP API with local auth and Electron service lifecycle
- Story 1.3: Config port, secrets layout, and SQLite app-data store
- Story 1.4: Design tokens, dark mode, and Russian app chrome shell
- Story 1.5: Calendar home empty chrome with side panel
- Story 1.6: Settings sections shell with explicit save

## Requirements & Constraints

- v1 is single-learner personal desktop (English target, Russian L1/explanations); no multi-user, no secrets in git.
- Never send surname, postal/physical address, email, or phone into LLM-bound context; API keys and Telegram identity stay out of prompts.
- Settings must be documented in-product for all v1-required options (LLM/API, Telegram linkage, schedule/reminders, duration/emphasis, voice); no undocumented hidden settings for normal use.
- UI and Telegram issue commands only; UI cache is never source of truth for Living plan or Progress (writes belong to teacher domain use cases in later epics).
- Closing the Electron window must not stop the teacher service (background delivery readiness).
- Entity IDs are opaque string UUIDs; learner fields include at least `target_language`, `L1`, `timezone` (v1 defaults `en` / `ru`).
- Success for this epic: app launches; service runs on loopback with local auth; Config/SQLite layout works; calendar empty chrome and Settings shells are usable; LLM/API keys persist via explicit save.

## Technical Decisions

- Layout: `apps/desktop/` (electron-vite / create-electron `vue-ts`: main, preload, Vue 3 renderer); `services/teacher/` installable package import name `teacher_service` at `src/teacher_service/{domain,ports,adapters/{api,persistence,llm,voice,telegram,config},graphs}/`. Pin Electron/Vue/Vite and Python ≥3.12 / FastAPI / LangGraph family at scaffold.
- Hexagonal: pedagogy/scheduling only in domain; domain depends on ports — no Vue, Electron, Telegram SDK, or vendor LLM/voice SDK imports in domain.
- Process topology: Python teacher is a background user service; Electron main is a thin host (window + start/attach/stop/status only). Domain traffic is loopback HTTP only — not Electron IPC as a domain bus. IPC is lifecycle only. Vue must not call a dead service silently — show stopped + error + retry.
- Trust: API binds loopback only; every HTTP request requires a local auth token (Bearer or equivalent). Token minted/loaded into OS app-data via Config — never hardcoded; Vue gets it via lifecycle/preload; clear/rotate invalidates prior tokens.
- Wire: JSON `snake_case` everywhere; errors `{ code, message, retryable }`. (SSE shares the same conventions later; not required for Epic 1 beyond health/status.)
- Persistence: SQLite sole durable store under one OS app-data directory shared by SQLite, secrets, and (later) voice-model cache; Config port owns secrets/toggles with single-user OS file permissions. Dev and installed builds resolve the same logical layout.
- If the teacher dies, Electron surfaces status and can restart; no multi-tenant cloud env in v1.
- Naming convention for domain entities/ports follows architecture spine (e.g. ports like Config; entities later). Dates: UTC ISO-8601 in storage/API; UI localizes via learner timezone.

## UX & Interaction Patterns

- Working-tool voice, not game/SaaS: cool grey chrome (`neutral-cool-lines`); coral is spark only — never body text on spark coral; filled CTAs use coral-cta + on-coral.
- Implement CSS variables for light + dark pairs: bg, surface, sidebar, ink, muted, line, coral, coral-cta, coral-soft, missed, done, on-coral, today-tint. Dark follows OS + manual override.
- Typography: `"Segoe UI", "Helvetica Neue", Arial, sans-serif`; nav/body sentence case; panel/section labels may be ALL CAPS. Shape: ~4px chrome radius; full round reserved for numbered steps/mic later.
- Russian UI chrome for nav (Calendar, Living plan, Progress, Settings); lesson content later is target language. Moderate motion; honor OS reduce-motion.
- Calendar home (default post-shell when not onboarding): Outlook-like timed week default, month available; Today / prev / next; today pill + current-time line; today-tint on today cell only. Empty grid — no fake demo events. Side panel beside calendar (not modal) with empty hint «выберите урок для просмотра краткой информации или истории». Minimal elevation (tonal/line, not multi-shadow).
- Settings: full-screen sections — Telegram, Voice, Schedule/duration, Goals/emphasis, LLM/API keys. Explicit «Сохранить» (not autosave); leave without save discards or confirms. Telegram: unlinked + «Привязать» (stub OK until Epic 4); no manual chat-id field. Voice/Schedule/Goals: visible placeholder/summary chrome only in this epic.

## Cross-Story Dependencies

- 1.1 → 1.2 → 1.3 (scaffold → loopback/auth/lifecycle → Config/SQLite).
- 1.4 needs desktop renderer from 1.1; 1.5 and 1.6 need the branded shell from 1.4.
- 1.6 LLM/API persist depends on Config from 1.3; Telegram/Voice/Schedule/Goals shells stay stubs for Epic 2/3/4 wiring.
- Epic 2 assumes this foundation for onboarding and calendar with real lessons; Epic 3 reads Voice prefs; Epic 4 completes Telegram link. Window-close-must-not-kill-service is a hard gate for Epic 4 delivery.
