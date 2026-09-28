---
title: "1.6 Settings sections shell with explicit save"
type: "feature"
created: "2026-09-28"
status: "done"
route: "dispatch"
review_loop_iteration: 0
baseline_commit: "a99d03109ad6f9efd893b3a2362e05d640ade60a"
context:
  - "{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md"
  - "{project-root}/_bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/EXPERIENCE.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Settings is still a title stub — Learners cannot see documented v1 options or persist LLM/API keys through Config (NFR4), and the desktop still has no Electron teacher lifecycle (or tray host-survival) to authenticate those saves without killing background readiness on window close.

**Approach:** Replace `#/settings` with a full-screen Russian sections shell; explicit «Сохранить» for LLM/API via authenticated loopback HTTP → Config; absorb Electron thin-host spawn/attach/stop/status, Config bearer seed before spawn, preload baseUrl/token, and tray-first host-survival so Vue can save for real while the teacher keeps running after window close; other Settings sections stay documented placeholder chrome.

**Decisions:**

- SECTIONS: single-scroll full-screen Settings (not drawer/tabs); ALL CAPS section kickers; sentence-case body; reuse `tokens.css` surfaces (UX-DR20)
- LLM_FIELD: one writable field — Config `llm_api_key` only (no provider/base-url until Config grows)
- SECRET_API: `GET /config/llm` → `{ "configured": true|false }`; `PUT /config/llm` body `{ "llm_api_key": "<non-empty>" }` → `{ "configured": true }`; empty/whitespace → 422 `{code,message,retryable}`; responses never echo the secret; writes call `set_secret(SECRET_LLM_API_KEY)`
- STUBS: Telegram unlinked + «Привязать» non-functional stub (no chat-id); Voice / Schedule+«изменить» / Goals = visible placeholder/summary chrome only (wire in 2.7 / 4.1)
- THEME: System/Light/Dark stays in shell nav footer — not a Settings body control
- LEAVE_DIRTY: confirm-save/leave dialog when navigating away with unsaved LLM edits — never silent persist
- AUTH_BRIDGE: Electron thin-host spawn/attach/stop/status + preload `base_url`+bearer + Vue authenticated save (closes deferred 1.2 spawn/token-bridge); domain traffic stays HTTP — IPC is lifecycle only
- BEARER_STORE: sole authority is Config `secrets/bearer_token` under app-data (`TEACHER_DATA_DIR` / platformdirs); Electron ensures a bearer exists (mint if missing) before spawn and passes the same value via env/Config resolve order — never a second authoritative store in Electron userData
- ATTACH: on launch, if loopback `GET /health` accepts the Config bearer → attach (reuse process); else spawn child with shared `TEACHER_DATA_DIR` + bearer; if something listens but token mismatches → fail closed (no silent wrong-token attach)
- REMINT: clearing app-data or rotating the bearer invalidates prior tokens; host remints into Config on next start
- HOST_SURVIVAL: tray-first — visible tray icon; closing the UI window hides it and must not stop the teacher; tray reopen restores the window; quit-from-tray (or equivalent explicit quit) stops the host and may stop the teacher
- LAUNCH_FAILURE_UI: on start/attach failure, show learner-visible stopped/error + retry (minimal shell/Settings banner — not polished global status chrome)

## Boundaries & Constraints

**Always:**

- Russian Settings chrome: sections for Telegram, Voice, Schedule/duration, Goals/emphasis, LLM/API with in-product labels/descriptions covering those v1 topics (NFR4 / UX-DR20)
- Explicit «Сохранить» for LLM/API — never autosave on keystroke; wire JSON `snake_case`; HTTP loopback only (no Electron IPC as domain bus)
- Persist LLM key only via Config port (`secrets/llm_api_key`, 0600); Bearer auth on every request; fail closed without token
- Electron main starts or attaches teacher, reports running/stopped via lifecycle IPC; Vue gets token+baseUrl via preload only (never embeds a committed secret)
- Bearer lives only in Config app-data; Electron may cache for the session but remint/writes go through Config
- Tray-first host-survival: window close → hide + keep teacher (override current `window-all-closed` → `app.quit()`); tray icon visible; reopen from tray; teacher stops only on explicit app quit
- Vue must not silently succeed against a dead/unreachable teacher — show error + retry on save failure; launch failure uses LAUNCH_FAILURE_UI
- Leave-dirty: confirm before leave when LLM fields dirty; discard only after confirm (or stay)
- Reuse shell/nav/`#/settings` route name; touch renderer + teacher API/Config + desktop main/preload as needed
- On Done: annotate resolved deferred-work rows (1.2 spawn/token-bridge, 1.2 host-survival, 1.2 remint-when-bridge-lands) with `resolved_by` this spec; HTTP LLM secret-write was Never in 1.3 — no fake “1.3 secret-write” ledger label; polished global status chrome may remain deferred

**Never:**

- Autosave; silent persist on navigate-away
- Manual Telegram chat-id field; functional Voice/Schedule/Goals persist (Epic 2.7); real Telegram deep-link (Epic 4.1)
- Return/log secret values in API JSON or UI after save; inject keys into LLM prompts
- Domain imports of Vue/Electron; SQLite writes from Vue; change Calendar home behavior
- Second authoritative bearer store in Electron userData
- Stop the teacher solely because the UI window closed
- Polished global teacher status chrome beyond LAUNCH_FAILURE_UI + Settings save/retry (still deferred from 1.2)

## I/O & Edge-Case Matrix

| Scenario              | Input / State                                        | Expected Output / Behavior                                                       | Error Handling                      |
| --------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------- | ----------------------------------- |
| Open Settings         | Nav → Настройки                                      | Full-screen five sections + LLM field + «Сохранить»; no calendar panel           | N/A                                 |
| Host start (spawn)    | App launch; nothing healthy on loopback              | Mint/load Config bearer; spawn teacher; tray up; preload baseUrl+bearer          | LAUNCH_FAILURE_UI; save blocked     |
| Host start (attach)   | Loopback `/health` OK with Config bearer             | Attach; tray up; preload same auth                                               | N/A                                 |
| Host start (mismatch) | Port open; Bearer rejects `/health`                  | Fail closed; no attach with wrong token                                          | LAUNCH_FAILURE_UI                   |
| Save LLM key          | Non-empty key + «Сохранить» + teacher running + auth | `PUT /config/llm` → Config `llm_api_key`; UI configured; no autosave             | N/A                                 |
| Save empty key        | Blank/whitespace + «Сохранить»                       | Client reject or 422; Config unchanged                                           | Clear validation copy               |
| Teacher down / 401    | Save while unreachable or bad token                  | No silent success; error + retry; Config unchanged                               | `{code,message,retryable}` surfaced |
| Stub Telegram         | View Telegram section                                | Unlinked + «Привязать» present; no chat-id; click no-ops/disabled                | N/A                                 |
| Stub other sections   | View Voice / Schedule / Goals                        | Placeholder/summary chrome + docs; Schedule «изменить» stub                      | N/A                                 |
| Leave dirty           | Unsaved LLM edits + navigate away                    | Confirm dialog; leave discards only after confirm; never silent persist          | Stay on cancel                      |
| Masked status         | Key already configured; reopen                       | `GET /config/llm` → `configured: true`; field empty/masked — raw key never shown | N/A                                 |
| Token remint          | Clear app-data / rotate bearer                       | Prior token rejected; host remints Config bearer on next start                   | 401 until remint                    |
| Window close          | Learner closes UI window                             | Window hides; tray remains; teacher keeps running                                | N/A                                 |
| Tray reopen           | Activate tray / reopen                               | Window restored; same preload auth; teacher still running                        | N/A                                 |
| Explicit quit         | Quit from tray (or equivalent)                       | App exits; teacher may stop with host                                            | N/A                                 |

</frozen-after-approval>

## Code Map

- `_bmad-output/implementation-artifacts/epic-1-context.md` — Settings + lifecycle constraints
- `_bmad-output/planning-artifacts/epics.md` (Story 1.6 + absorbed 1.2 lifecycle/host-survival ACs) — AC source
- `_bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/EXPERIENCE.md` — sections + explicit «Сохранить»
- `_bmad-output/implementation-artifacts/deferred-work.md` — resolve 1.2 spawn/token-bridge + host-survival + remint-on-bridge; leave polished status chrome deferred
- `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md` — API auth continuity
- `_bmad-output/implementation-artifacts/spec-1-3-config-port-secrets-layout-and-sqlite-app-data-store.md` — Config bearer + `llm_api_key`
- `_bmad-output/implementation-artifacts/spec-1-5-calendar-home-empty-chrome-with-side-panel.md` — `#/settings` stub continuity
- `apps/desktop/src/main/index.ts` — today quits on `window-all-closed`; replace with spawn/attach/stop/status, Config bearer seed, tray hide/reopen/quit
- `apps/desktop/src/preload/index.ts` + `index.d.ts` — expose `base_url`, bearer, lifecycle status (no domain bus)
- `apps/desktop/src/renderer/src/router/index.ts` — point `settings` at SettingsView
- `apps/desktop/src/renderer/src/views/TitleStubView.vue` — keep for План/Прогресс
- `apps/desktop/src/renderer/src/App.vue` / `styles/tokens.css` / `composables/useTheme.ts` — reuse; theme stays in nav
- `apps/desktop/src/renderer/src/App.spec.ts` — update Settings + leave-dirty + launch-failure expectations
- New: `apps/desktop/src/renderer/src/views/SettingsView.vue` (+ section components as needed)
- New: `apps/desktop/src/renderer/src/services/teacherClient.ts` (or equivalent) — `GET`/`PUT /config/llm` via preload auth
- New: leave-dirty guard (router `beforeEach` and/or SettingsView navigation guard)
- `services/teacher/src/teacher_service/ports/config.py` + `adapters/config/layout.py` — reuse `get_secret`/`set_secret` / `SECRET_LLM_API_KEY` / `SECRET_BEARER_TOKEN`
- `services/teacher/src/teacher_service/adapters/api/app.py` — add `GET`/`PUT /config/llm`; keep Bearer middleware
- `services/teacher/tests/test_config_llm_api.py` (or extend existing) — HTTP→Config I/O matrix; no secret echo

## Tasks & Acceptance

**Execution:**

- [x] `apps/desktop/src/main/index.ts` — spawn/attach/stop/status; seed Config bearer; tray-first hide/reopen/quit; stop quitting on `window-all-closed` — AUTH_BRIDGE + HOST_SURVIVAL
- [x] `apps/desktop/src/preload/index.ts` + `index.d.ts` — expose `base_url`, bearer, running/stopped status — AUTH_BRIDGE
- [x] `services/teacher/src/teacher_service/adapters/api/app.py` — `GET`/`PUT /config/llm` via Config; no secret echo — SECRET_API
- [x] `services/teacher/tests/` — prove save/empty/401/configured mask + remint reject — I/O matrix
- [x] `apps/desktop/src/renderer/src/views/SettingsView.vue` (+ sections) — five documented sections; LLM + «Сохранить»; stubs; LAUNCH_FAILURE_UI surface as needed — UX-DR17/NFR4
- [x] `apps/desktop/src/renderer/src/router/index.ts` + `services/teacherClient.ts` — wire `#/settings`; preload auth; dead-service error+retry — AD-2/AD-4
- [x] Leave-dirty confirm (router/`SettingsView` guard) — LEAVE_DIRTY
- [x] `apps/desktop/src/renderer/src/App.spec.ts` (+ Settings/lifecycle specs) — unit-test I/O matrix rows — Verification
- [x] `npm test` / `typecheck` / `build` + `uv run pytest` — Verification
- [x] On Done: `sprint-status.yaml` 1-6 → review; `resolved_by` on 1.2 spawn/host-survival/remint deferred-work rows — sprint sync

**Acceptance Criteria:**

- Given the shell, when the Learner opens Настройки, then full-screen Telegram / Voice / Schedule/duration / Goals/emphasis / LLM/API sections appear with Russian documented labels and ALL CAPS section kickers (NFR4 / UX-DR20)
- Given Electron thin host, when the app starts, then main spawns or attaches the teacher per ATTACH, tray is present, Vue obtains bearer+baseUrl via preload only, and bearer authority is Config app-data
- Given LLM/API fields, when the Learner enters a key and presses «Сохранить» with teacher running, then `PUT /config/llm` persists `llm_api_key` with no autosave and no secret echo
- Given Telegram / Voice / Schedule / Goals, when viewed in Epic 1, then placeholder/summary chrome is visible; Telegram is unlinked with stub «Привязать» and no chat-id
- Given unsaved LLM edits, when navigating away, then a confirm dialog appears and changes never silently persist
- Given teacher down or unauthorized, when save is attempted, then UI shows error + retry and Config is unchanged
- Given teacher start/attach failure on launch, when the UI loads, then the Learner sees stopped/error + retry (LAUNCH_FAILURE_UI) and must not silently call authenticated HTTP successfully
- Given app-data clear or bearer rotate, when the prior token is presented, then it is rejected until the host remints Config bearer on next start
- Given a running teacher, when the Learner closes the UI window, then the window hides, tray remains, and the teacher is not stopped; tray reopen restores the window; explicit quit may stop the teacher with the host

## Implementation Notes

- Review patch (pre-approval): bearer authority = Config only; SECRET_API paths locked; ATTACH + LAUNCH_FAILURE_UI + remint ACs added; tasks use concrete paths; `baseline_commit` set to `a99d031…`.
- **Teacher API (SECRET_API):** `services/teacher/src/teacher_service/adapters/api/app.py` now stores the resolved `ConfigPort` on `app.state.config` and adds `GET /config/llm` (`{"configured": bool}`) and `PUT /config/llm` (pydantic `LlmConfigUpdate`, blank/whitespace `llm_api_key` rejected via `field_validator` → existing `RequestValidationError` handler → 422 `{code,message,retryable}`). Writes go through `FileConfig.set_secret(SECRET_LLM_API_KEY, ...)` only; responses never include the raw key. New `services/teacher/tests/test_config_llm_api.py` (10 tests) proves unconfigured-default, save+mask, blank-key 422 + Config-unchanged, 401 without/with-wrong token, and Bearer remint rejecting the prior token on this route. Full suite: `uv run pytest` → 49 passed.
- **Electron thin host (AUTH_BRIDGE / HOST_SURVIVAL / ATTACH / REMINT):** New Electron-free `apps/desktop/src/main/teacherHost.ts` owns `resolveDataDir` (linux/macOS/Windows platformdirs-equivalent, `TEACHER_DATA_DIR` override), Config-secrets bearer mint/read/write (`secrets/bearer_token`, 0700/0600 perms — sole authority, no second userData store), `checkHealth` (ok/unauthorized/unreachable), spawn-command resolution (`uv run teacher-api` in `services/teacher`, `TEACHER_SERVICE_DIR` override), and the `TeacherHost` class (attach-if-healthy, fail-closed on token mismatch, else spawn + poll, `stop()` only kills a process it spawned). `apps/desktop/src/main/index.ts` wires this into Electron: tray icon (embedded coral-mark PNG) with «Открыть»/«Выход», `window-all-closed` is now a no-op (window `close` hides instead), and `before-quit` stops only an owned child. `apps/desktop/src/preload/index.ts` + `index.d.ts` expose `window.teacher.{getAuth,retry,onStatusChange}` (`base_url`/`bearer`/`state` — lifecycle IPC only, no domain bus). 18 new node-environment unit tests in `apps/desktop/src/main/teacherHost.spec.ts` cover data-dir resolution per platform, mint/reuse/remint, health tri-state, command resolution + override, and the attach/fail-closed/spawn/timeout/stop paths via injected fake `fetch`/`spawn`.
- **Settings shell (SECTIONS / LEAVE_DIRTY / stubs):** New `apps/desktop/src/renderer/src/views/SettingsView.vue` — single-scroll full-screen shell reusing `tokens.css` surfaces; ALL CAPS kickers (TELEGRAM / ГОЛОС / РАСПИСАНИЕ И ДЛИТЕЛЬНОСТЬ / ЦЕЛИ И АКЦЕНТЫ / LLM / API); Telegram unlinked + disabled «Привязать» stub (no chat-id), disabled «Изменить» schedule stub, Voice/Goals placeholder copy; LLM field is always empty/masked on load (`GET /config/llm` only toggles a "already saved" hint) with explicit «Сохранить» (client-side blank-key validation before any fetch — no autosave); save error/retry surfaces the teacher's `{code,message,retryable}` without clearing the input; a minimal LAUNCH_FAILURE_UI banner + «Повторить» appears whenever `state !== 'running'` (calls `window.teacher.retry()`); `onBeforeRouteLeave` confirms via `window.confirm` only when the LLM field is dirty, staying on cancel. New `apps/desktop/src/renderer/src/services/teacherClient.ts` wraps preload auth + `fetch` with a shaped `TeacherApiError` (never silently succeeds against a dead/unreachable teacher). Router (`router/index.ts`) now points `settings` at `SettingsView`; `plan`/`progress` stay `TitleStubView`.
- **Tests:** `apps/desktop/src/renderer/src/views/SettingsView.spec.ts` (9 tests, mounted through a real `<router-view>` so `onBeforeRouteLeave` attaches) covers stub chrome, masked-status load, blank-key rejection with no PUT, save+mask+no-autosave, 401 error+retry with input preserved, LAUNCH_FAILURE_UI+retry, and both leave-dirty branches (cancel stays / confirm leaves) plus the no-dirty no-prompt case. `apps/desktop/src/renderer/src/services/teacherClient.spec.ts` (6 tests) covers the HTTP/error-shaping layer directly. `App.spec.ts` updated: `plan`/`progress` stay in the title-only stub loop (Settings no longer is one); added a Settings-sections-shell assertion (no calendar panel, five kickers, theme control still present via the nav-footer chrome that lives outside `<RouterView>`). Added `src/renderer/src/test-setup.ts` (default `window.teacher` + `fetch` mocks, guarded to no-op outside `happy-dom`) and switched `vitest.config.ts` to `environmentMatchGlobs` so `src/main/**/*.spec.ts` runs under `node` (Vitest logs this option as deprecated in favor of `test.projects`; kept for now — functionally correct, low risk to revisit later). Full run: `npm test` → 65 passed (6 files); `npm run typecheck` clean; `npm run build` clean.
- **Not verified in this pass:** the actual Electron GUI (tray icon rendering, real spawn of `uv run teacher-api`, window-hide-on-close, tray reopen, quit-stops-child) was not exercised end-to-end — this sandbox has no `Xvfb`/VNC runtime available in the working shell (`xvfb-run: not found`; `AGENTS.md`'s documented `npm run preview:xvfb` / port-6080 path needs the `desktop-lite` devcontainer feature active in an interactive session). Lifecycle *decision logic* is unit-tested: `teacherHost.spec.ts` (attach/fail-closed/spawn/timeout/stop) plus `hostSurvival.spec.ts` (window-close hide vs allow-close, quit stop-owned vs leave-attached, `window-all-closed` never quits). Flagged as a residual manual-verification gap, not a deferred-work ledger item, since the spec's required Verification commands (`npm test`/`typecheck`/`build`, `uv run pytest`) all pass.

## Spec Change Log

## Review Triage Log

- false — Blind: new-file hunks rooted at `src/main/…` would land outside the app — disproved: `git diff --no-index` cwd artifact; files exist under `apps/desktop/src/…` and vitest finds them
- false — Blind: unified review diff omitted teacher `/config/llm` — disproved: incomplete first diff (cwd); `app.py` + `test_config_llm_api.py` present; pytest green
- medium — Blind/Edge: `TeacherHost.start()` leaves spawned child alive when `waitForHealth` fails — verified: lines 253–260 set error without `stop()` — route patch
- medium — Blind/Edge/VG-other: `onStatusChange` assigns `auth` but never `loadLlmStatus()` — verified SettingsView.vue:86–88 — route patch
- false — Blind: REMINT only mints when secret absent — disproved: Intent remint is clear-app-data / next-start mint; rotate covered by Config rewrite + pytest remint case
- low — Blind: save-failure UI lacks a dedicated retry control — rejected: «Сохранить» re-click is the retry; LAUNCH_FAILURE has «Повторить»; fix would add UI complexity without demonstrated gap
- false — Blind/Edge: `before-quit` sets `isQuitting` with no reset if quit cancelled — disproved: nothing calls `event.preventDefault()` on `before-quit` in this host
- low — Blind: duplicated `TeacherStatus` types across preload/host/client — rejected: no demonstrated drift; shared package would add surface
- false — Blind: IPC status push includes bearer — disproved: AUTH_BRIDGE Intent requires Vue obtain bearer via preload; push mirrors `getAuth` payload
- low — Blind: global `test-setup` fetch stub — rejected: unlikely everyday product harm; harness convenience
- low — Blind: `hostSurvival` “Tray reopen” only re-asserts `windowCloseAction` — rejected with VG HOST_SURVIVAL defer (Electron wiring)
- medium — Blind: `writeBearerToken` chmods entire `dataDir` — verified teacherHost.ts:82 — route patch
- low — Blind: spawned `stdio: 'ignore'` hides spawn logs — rejected: intentional default; not everyday learner harm
- medium — Blind/Edge: overlapping `start()`/`retry` can orphan prior child — verified no in-flight guard — route patch
- low — Blind: `toApiError` maps JSON-parse fail to `network_error` — rejected: rare; message still surfaces
- medium — Edge: `checkHealth` fetch has no AbortSignal timeout — verified teacherHost.ts:113–115 — route patch
- medium — Edge: spawned child has no `error` listener — verified spawnChild only listens `exit` — route patch
- medium — Edge: `refreshStatus`/`retry` lack try/finally — verified SettingsView.vue:42–54 — route patch
- low — Edge: double-click Save before `saving` flag — route patch (trivial early return)
- medium — Edge: 2xx `response.json()` parse can throw raw — verified teacherClient.ts:106,121 — route patch
- low — Edge: status push after destroyed window — route patch (trivial `isDestroyed` guard)
- medium — VG: TeacherHost running status never asserts `bearer`/`base_url` — pre-verified — route patch
- defer — VG: HOST_SURVIVAL Electron wiring in `index.ts` untested beyond helpers — pre-verified disposition defer
- medium — VG: preload/main IPC channel strings fully mocked — pre-verified — route patch
- medium — VG: LAUNCH_FAILURE retry test only asserts mock call — pre-verified — route patch
- medium — VG: `onStatusChange` subscription untested — pre-verified — route patch
- medium — VG: child `exit` → stopped untested — pre-verified — route patch
- medium — VG: LLM `load-error` UI untested — pre-verified — route patch

## Design Notes

Layout: single scroll of `{colors.surface}` blocks on `{colors.bg}`; coral-cta on «Сохранить» / «Привязать». Schedule: summary placeholder + stub «изменить». Tray: app icon; menu at least «Открыть» + «Выход». Lifecycle IPC: status + token/baseUrl only — Settings save uses `fetch` to `http://127.0.0.1:8765`. Discover teacher via `teacher-api` / `python -m teacher_service.adapters.api`; set `TEACHER_DATA_DIR` (or rely on platformdirs) so host and child share Config. Dev attach: if a manually started `teacher-api` already serves `/health` with the same Config bearer, reuse it.

## Verification

**Commands:**

- `cd services/teacher && uv run pytest` — expected: `/config/llm` write/mask/auth tests green — **ran: 49 passed** (39 prior + 10 new in `test_config_llm_api.py`)
- `cd apps/desktop && npm test && npm run typecheck && npm run build` — expected: Settings + lifecycle client tests green; clean typecheck + build — **ran: 72 passed across 7 files** (`teacherHost.spec.ts` 19, `hostSurvival.spec.ts` 4, `calendarDates.spec.ts` 10, `teacherClient.spec.ts` 6, `useTheme.spec.ts` 8, `SettingsView.spec.ts` 11, `App.spec.ts` 14); `typecheck` clean; `build` clean

**Manual checks:**

- Launch app → tray + teacher up → Settings save round-trip; leave-dirty confirm; stubs do not persist; theme still in nav — **not run**: no `Xvfb`/VNC runtime available in this session (see Implementation Notes); decision logic covered by `teacherHost.spec.ts` + `SettingsView.spec.ts` instead
- Close window → teacher still listening on loopback; tray reopen restores UI; Quit stops host — **not run** (same constraint)
- Kill/break teacher → LAUNCH_FAILURE_UI or save error+retry; no silent success — **not run end-to-end**; unit-covered via `SettingsView.spec.ts` (401 during save, `state !== 'running'` on load)
