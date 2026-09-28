# Deferred work

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-scaffold-electron-vue-desktop-and-python-teacher-package.md`
  summary: Document Linux Electron system library needs (e.g. libatk) in AGENTS.md desktop start notes
  evidence: Electron failed here with missing libatk-1.0.so.0; review deferred because the fix edits AGENTS.md agent-context

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-scaffold-electron-vue-desktop-and-python-teacher-package.md`
  summary: Automated proof that desktop main/preload start without a live teacher beyond npm run build
  evidence: verification-gap — build would stay green if a hard teacher dependency were added; revisit with static coupling scan or smoke in 1.2 lifecycle

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-scaffold-electron-vue-desktop-and-python-teacher-package.md`
  summary: Party-mode memlog changes mixed into the 1.1 working tree
  evidence: `_bmad-output/party-mode/memories/installed/.memlog.md` is outside the story Code Map; keep memory, do not treat as scaffold deliverable when committing

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md`
  summary: Electron host-survival UX when the UI window closes (tray and/or hide-without-tray reopen/attach; teacher must not stop solely because the window closed)
  evidence: Split from 1.2 to keep the draft under the token budget; core loopback API + auth + spawn remains in-spec; AD-2 window-close gate moves here with the visible host model choice
  resolved_by: spec-1-6-settings-sections-shell-with-explicit-save.md

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md`
  summary: Learner-visible stopped/error/retry chrome (copy language and UI) when teacher start/attach fails
  evidence: Split from 1.2 with host-survival UX; narrowed 1.2 proves lifecycle status + health over HTTP without polished status chrome (Story 1.4 may also own Russian chrome)
  resolved_by: spec-1-6-settings-sections-shell-with-explicit-save.md (minimal Settings-banner LAUNCH_FAILURE_UI; polished global status chrome stays deferred)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md`
  summary: Electron thin-host spawn/attach/stop/status, userData token mint/load bridge, preload token/base_url surface, and Vue GET /health smoke when running
  evidence: Second split from 1.2 to fit the token budget; narrowed spec ships teacher loopback FastAPI + Bearer auth + health + pytest only
  resolved_by: spec-1-6-settings-sections-shell-with-explicit-save.md (bridge lands with Config as the sole bearer authority — no second userData store, per the locked 1.6 Intent)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md`
  summary: Strengthen AGENTS.md unauthenticated health smoke to assert error JSON body shape `{code,message,retryable}` not only HTTP status
  evidence: Review triage deferred because the fix edits agent-context AGENTS.md

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md`
  summary: When Electron token bridge lands, explicitly cover remint/rotate and invalidate-on-clear of prior Bearer tokens (epic Story 1.2 AC)
  evidence: Review found remint/rotation not parked beyond userData mint/load in deferred Electron spawn entry
  resolved_by: spec-1-6-settings-sections-shell-with-explicit-save.md

## Deferred from: code review of spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md (2026-09-24)

- Align older deferred-work evidence strings that still say Electron spawn / “lifecycle status” remains in-spec with the frozen Intent (API-auth only; Electron deferred)
- Add pytest (or install-time) resolution of `teacher-api` console script and/or `python -m teacher_service.adapters.api` so miswired entrypoints cannot stay green while direct `cli.main` tests pass
- CLI: catch `OSError` from `uvicorn.run` (e.g. port busy) and exit controlled with stderr instead of a raw traceback

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-config-port-secrets-layout-and-sqlite-app-data-store.md`
  summary: Authenticated HTTP snake_case learner/profile (or config-status) read projection over SQLite/Config
  evidence: Split from 1.3 to fit the token budget; narrowed 1.3 proves Config app-data layout, secrets (incl. Bearer via Config), and SQLite Learner create/load via ports/tests — epic Story 1.3 API projection AC remains open here

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-config-port-secrets-layout-and-sqlite-app-data-store.md`
  summary: Document an operable AGENTS.md bootstrap to create Config `bearer_token` without Settings UI or TEACHER_AUTH_TOKEN-only path
  evidence: Review found Config-backed listen documented but no step to mint/write bearer_token under app-data before Story 1.6; fix edits agent-context AGENTS.md

## Deferred from: code review of spec-1-3-config-port-secrets-layout-and-sqlite-app-data-store.md (2026-09-27)

- AGENTS Config `bearer_token` bootstrap still undocumented (agent-context AGENTS.md; already tracked above for the same source_spec)
- Epic Story 1.3 in `epics.md` still presents authenticated learner/profile HTTP AC without a deferral cross-reference to deferred-work / narrowed 1.3 Intent

- source_spec: `_bmad-output/implementation-artifacts/spec-1-4-design-tokens-dark-mode-and-russian-app-chrome-shell.md`
  summary: Russian working-tool app chrome shell (nav Календарь/План/Прогресс/Настройки, vue-router placeholder routes, reduce-motion route transitions)
  evidence: Split from 1.4 to fit the token budget; narrowed 1.4 ships design tokens + dark mode (OS + manual) on the existing renderer surface — epic Story 1.4 Russian shell / UX-DR20 nav AC remains open here (needed before 1.5/1.6)
  resolved_by: spec-1-5-calendar-home-empty-chrome-with-side-panel.md

## Deferred from: code review of spec-1-4-design-tokens-dark-mode-and-russian-app-chrome-shell.md (2026-09-27)

- Epic Story 1.4 in `epics.md` still presents Russian chrome / UX-DR20 ACs without a deferral cross-reference to deferred-work / narrowed 1.4 Intent
- AGENTS.md desktop verify path still omits `npm test` / Vitest after the first renderer test harness (agent-context AGENTS.md)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-5-calendar-home-empty-chrome-with-side-panel.md`
  summary: Production `main.ts` hash-router `.use(createAppRouter())` install is not executed by vitest (App.spec injects its own router)
  evidence: Verification-gap review; removing `.use(router)` from main would leave all App.spec suites green; low-leverage entry smoke for this chrome story

- source_spec: `_bmad-output/implementation-artifacts/spec-1-6-settings-sections-shell-with-explicit-save.md`
  summary: Electron main HOST_SURVIVAL wiring (close→hide, window-all-closed no-quit, tray quit→isQuitting, before-quit stop-owned) lacks an Electron harness test beyond pure hostSurvival helpers
  evidence: Verification-gap review; hostSurvival.spec.ts covers decisions only; demonstrating index.ts regressions needs Electron main test runtime unavailable in this sandbox

## Deferred from: code review of spec-1-6-settings-sections-shell-with-explicit-save.md (2026-09-28)

- HOST_SURVIVAL Electron main wiring untested beyond hostSurvival helpers — needs Electron main harness (already ledgered above; reconfirmed this review)
- AUTH_BRIDGE main/preload IPC handlers never executed in tests — same Electron-host harness cost; Vue/HTTP covered against mock contract
- AGENTS.md still says Electron spawn/host-survival remain deferred — fix edits agent-context AGENTS.md
