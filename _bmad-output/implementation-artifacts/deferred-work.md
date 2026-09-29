# Deferred work

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-scaffold-electron-vue-desktop-and-python-teacher-package.md`
  summary: Document Linux Electron system library needs (e.g. libatk) in AGENTS.md desktop start notes
  evidence: Electron failed here with missing libatk-1.0.so.0; review deferred because the fix edits AGENTS.md agent-context
  resolved_by: AGENTS.md Dev Container GUI — Linux Electron system libraries (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-scaffold-electron-vue-desktop-and-python-teacher-package.md`
  summary: Automated proof that desktop main/preload start without a live teacher beyond npm run build
  evidence: verification-gap — build would stay green if a hard teacher dependency were added; revisit with static coupling scan or smoke in 1.2 lifecycle
  resolved_by: desktopIndependence.spec.ts — static coupling scan + TeacherHost constructor smoke (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-scaffold-electron-vue-desktop-and-python-teacher-package.md`
  summary: Party-mode memlog changes mixed into the 1.1 working tree
  evidence: `_bmad-output/party-mode/memories/installed/.memlog.md` is outside the story Code Map; keep memory, do not treat as scaffold deliverable when committing
  resolved_by: process note only — not product work; closed as skip/moot (2026-09-29)

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
  resolved_by: AGENTS.md teacher smoke — curl | tee + jq keys assert (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md`
  summary: When Electron token bridge lands, explicitly cover remint/rotate and invalidate-on-clear of prior Bearer tokens (epic Story 1.2 AC)
  evidence: Review found remint/rotation not parked beyond userData mint/load in deferred Electron spawn entry
  resolved_by: spec-1-6-settings-sections-shell-with-explicit-save.md

## Deferred from: code review of spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md (2026-09-24)

- Align older deferred-work evidence strings that still say Electron spawn / “lifecycle status” remains in-spec with the frozen Intent (API-auth only; Electron deferred)
  resolved: 2026-09-29 — editorial; historical evidence left as written; resolved_by lines on those entries supersede
- Add pytest (or install-time) resolution of `teacher-api` console script and/or `python -m teacher_service.adapters.api` so miswired entrypoints cannot stay green while direct `cli.main` tests pass
  resolved: 2026-09-29 — `test_teacher_api_console_script_resolves` + `test_adapters_api_main_module_imports` in test_scaffold_imports.py
- CLI: catch `OSError` from `uvicorn.run` (e.g. port busy) and exit controlled with stderr instead of a raw traceback
  resolved: 2026-09-29 — cli.py SystemExit(1) + `test_cli_oserror_from_uvicorn_exits_controlled`

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-config-port-secrets-layout-and-sqlite-app-data-store.md`
  summary: Authenticated HTTP snake_case learner/profile (or config-status) read projection over SQLite/Config
  evidence: Split from 1.3 to fit the token budget; narrowed 1.3 proves Config app-data layout, secrets (incl. Bearer via Config), and SQLite Learner create/load via ports/tests — epic Story 1.3 API projection AC remains open here
  resolved_by: spec-2-1-onboarding-wizard-greeting-goals-interests-duration-schedule.md (partial — intake subset GET/PATCH /learner only; broader profile/config-status projection may still expand later)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-config-port-secrets-layout-and-sqlite-app-data-store.md`
  summary: Document an operable AGENTS.md bootstrap to create Config `bearer_token` without Settings UI or TEACHER_AUTH_TOKEN-only path
  evidence: Review found Config-backed listen documented but no step to mint/write bearer_token under app-data before Story 1.6; fix edits agent-context AGENTS.md
  resolved_by: AGENTS.md teacher Running — Config `set_secret(SECRET_BEARER_TOKEN, …)` bootstrap (2026-09-29)

## Deferred from: code review of spec-1-3-config-port-secrets-layout-and-sqlite-app-data-store.md (2026-09-27)

- AGENTS Config `bearer_token` bootstrap still undocumented (agent-context AGENTS.md; already tracked above for the same source_spec)
  resolved: 2026-09-29 — same AGENTS bootstrap as source_spec entry above
- Epic Story 1.3 in `epics.md` still presents authenticated learner/profile HTTP AC without a deferral cross-reference to deferred-work / narrowed 1.3 Intent
  resolved: 2026-09-29 — epics.md Story 1.3 AC footnote → deferred-work / 2.1 partial

- source_spec: `_bmad-output/implementation-artifacts/spec-1-4-design-tokens-dark-mode-and-russian-app-chrome-shell.md`
  summary: Russian working-tool app chrome shell (nav Календарь/План/Прогресс/Настройки, vue-router placeholder routes, reduce-motion route transitions)
  evidence: Split from 1.4 to fit the token budget; narrowed 1.4 ships design tokens + dark mode (OS + manual) on the existing renderer surface — epic Story 1.4 Russian shell / UX-DR20 nav AC remains open here (needed before 1.5/1.6)
  resolved_by: spec-1-5-calendar-home-empty-chrome-with-side-panel.md

## Deferred from: code review of spec-1-4-design-tokens-dark-mode-and-russian-app-chrome-shell.md (2026-09-27)

- Epic Story 1.4 in `epics.md` still presents Russian chrome / UX-DR20 ACs without a deferral cross-reference to deferred-work / narrowed 1.4 Intent
  resolved: 2026-09-29 — epics.md Story 1.4 AC footnote → deferred-work / absorbed by 1.5
- AGENTS.md desktop verify path still omits `npm test` / Vitest after the first renderer test harness (agent-context AGENTS.md)
  resolved: 2026-09-29 — already present in AGENTS.md (`npm test` (Vitest) and `npm run build`); confirmed closed

- source_spec: `_bmad-output/implementation-artifacts/spec-1-5-calendar-home-empty-chrome-with-side-panel.md`
  summary: Production `main.ts` hash-router `.use(createAppRouter())` install is not executed by vitest (App.spec injects its own router)
  evidence: Verification-gap review; removing `.use(router)` from main would leave all App.spec suites green; low-leverage entry smoke for this chrome story
  resolved_by: main.spec.ts — static assert createApp(App).use(createAppRouter()).mount (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-6-settings-sections-shell-with-explicit-save.md`
  summary: Electron main HOST_SURVIVAL wiring (close→hide, window-all-closed no-quit, tray quit→isQuitting, before-quit stop-owned) lacks an Electron harness test beyond pure hostSurvival helpers
  evidence: Verification-gap review; hostSurvival.spec.ts covers decisions only; demonstrating index.ts regressions needs Electron main test runtime unavailable in this sandbox
  resolved_by: electronMainWiring.spec.ts — static HOST_SURVIVAL index.ts wiring assert (2026-09-29; full Electron GUI harness still out of sandbox)

## Deferred from: code review of spec-1-6-settings-sections-shell-with-explicit-save.md (2026-09-28)

- HOST_SURVIVAL Electron main wiring untested beyond hostSurvival helpers — needs Electron main harness (already ledgered above; reconfirmed this review)
  resolved: 2026-09-29 — electronMainWiring.spec.ts static wiring (same as source_spec entry above)
- AUTH_BRIDGE main/preload IPC handlers never executed in tests — same Electron-host harness cost; Vue/HTTP covered against mock contract
  resolved: 2026-09-29 — electronMainWiring.spec.ts static main+preload scan + mocked preload invoke/on execution
- AGENTS.md still says Electron spawn/host-survival remain deferred — fix edits agent-context AGENTS.md
  resolved_by: epic-1-retro-2026-09-28.md (action item 2 — Running section updated 2026-09-28)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-onboarding-wizard-greeting-goals-interests-duration-schedule.md`
  summary: Outlook-like week-grid schedule UI (visual week chrome / click-to-add slots) reusable for Settings «изменить» mini-wizard
  evidence: Split from 2.1 to fit the token budget; narrowed 2.1 ships intake wizard with a compact weekday+time slot list editor and the same slot persistence model — epic Outlook week-grid chrome AC remains open here (needed before/with 2.7 Settings schedule edit)
  resolved_by: spec-2-1-outlook-week-grid-schedule.md (partial — onboarding grid + ScheduleWeekGrid extract; Settings mini-wizard mount remains 2.7; calendar lesson layout not claimed)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-placement-briefing-written-listening-speaking.md`
  summary: Rich listening player scrub/seek/replay-from-position UI (full EXPERIENCE listening player)
  evidence: Split from 2.3 to fit the token budget; narrowed 2.3 ships play/pause + comprehension questions only for placement listening
  resolved_by: spec-2-3-listening-player-scrub-seek-replay.md

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-placement-briefing-written-listening-speaking.md`
  summary: Optional cloud Voice fallback behind VoicePort (AD-9)
  evidence: Split from 2.3; narrowed story ships local-first STT/TTS only for placement seedable results

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-placement-briefing-written-listening-speaking.md`
  summary: Adaptive multi-form placement bank / re-take flows after first completion
  evidence: Split from 2.3; narrowed story persists one LLM-generated item set per learner placement run

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-placement-briefing-written-listening-speaking.md`
  summary: Pronunciation/intonation scoring beyond transcript + simple aggregate placement score (Epic 3.7)
  evidence: Split from 2.3; speaking seedability requires real local STT transcript stored — detailed pronunciation feedback stays Epic 3

- source_spec: `_bmad-output/implementation-artifacts/spec-2-3-placement-briefing-written-listening-speaking.md`
  summary: Production OpenAiLlmAdapter / LocalVoiceAdapter never executed under pytest (only Fake\* ports)
  evidence: Verification-gap review; fabricate-on-error in real adapters would leave placement API suite green; settle with thin adapter unit/integration smoke later
  resolved_by: test_llm_adapter.py + expanded test_voice_adapter.py — mocked HTTP / stand-in CLI smoke (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-4-living-plan-creation-and-persistence.md`
  summary: Bounded THREE+SERVER plan-create failure pause (`plan_create_failures`, 409 `plan_create_paused`, `reset_failures` «Повторить», paused UI state)
  evidence: Split from 2.4 to fit the token budget; narrowed 2.4 ships happy-path create + Config block + simple LLM error retry without a server fail-count pause — epic NFR3 bounded-pause AC remains open here

- source_spec: `_bmad-output/implementation-artifacts/spec-2-4-living-plan-creation-and-persistence.md`
  summary: LessonRecord richness beyond schedule projection (`living_plan_id`, `status`, optional `topic` stub) for Story 2.6 calendar consumers
  evidence: Split from 2.4 to fit the token budget; narrowed 2.4 persists lessons with `id` / `scheduled_at` / `timezone` only — 2.6 may require the richer columns

- source_spec: `_bmad-output/implementation-artifacts/spec-2-4-living-plan-creation-and-persistence.md`
  summary: WEEK_FILL DST/invalid-IANA hardening (spring gap skip, fall-back fold pick, bad timezone → `schedule_unusable`)
  evidence: Split from 2.4 to fit the token budget; narrowed 2.4 covers empty slots and zero hits in `[now, now+7d)` only

- source_spec: `_bmad-output/implementation-artifacts/spec-2-4-living-plan-creation-and-persistence.md`
  summary: Desktop onboarding plan view — replace OnboardingPlanStub with `config_blocked`/`creating`/`ready`/`error` UI, auto-POST, READONLY path cards + «план готов», GET resume chrome (UX-DR13)
  evidence: Second split from 2.4 to fit the token budget; narrowed 2.4 ships teacher domain/API/persistence + `plan_complete` on learner/gate types only — stub remains until this deferred UI lands

- source_spec: `_bmad-output/implementation-artifacts/spec-2-4-living-plan-creation-and-persistence.md`
  summary: Automated coverage of UNIQUE(learner_id) race → domain reload idempotent path in create_living_plan
  evidence: Review found only raw SQL IntegrityError coverage; concurrent POST loser branch (living_plan.py except/reload) is untested; v1 single-learner desktop makes real races unlikely
  resolved_by: test_living_plan_create_race.py — RaceStore IntegrityError + reload winner / empty fail (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-4-living-plan-creation-and-persistence.md`
  summary: Recompute WEEK_FILL after LLM returns so slow proposes cannot persist lesson times already in the past
  evidence: maybe-false medium from edge-case review; settle by injecting a clock that advances across a slot boundary during propose and asserting recomputed scheduled_at
  resolved_by: create_living_plan now_provider + post-LLM WEEK_FILL; test_living_plan_week_fill_recompute.py (2026-09-29)

- source_spec: `_bmad-output/implementation-artifacts/spec-2-4-living-plan-creation-and-persistence.md`
  summary: Enable SQLite PRAGMA foreign_keys=ON so lesson_record → living_plan FK is enforced
  evidence: Story 2.4 added the FK declaration but the store never enables foreign_keys (pre-existing pattern); orphan lesson rows remain possible
  resolved_by: SqliteStore.\_connect PRAGMA foreign_keys=ON + test_sqlite_foreign_keys_pragma_on (2026-09-29)
