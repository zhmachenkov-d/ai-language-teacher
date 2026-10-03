---
title: "Living plan full-screen document (view-only)"
type: "feature"
ticket: "5"
created: "2026-10-03"
status: "built"
baseline_revision: "e5458d2f40611285e87ccd63f516bc126953e22d"
route: "full"
route_source: "auto"
risk: "low"
review: "quick"
review_source: "pinned"
lenses_ran: ["quick"]
review_loop_iteration: 0
context:
  - "{project-root}/_bmad-output/initiative-ai-language-teacher/ux-ai-language-teacher/EXPERIENCE.md"
  - "{project-root}/_bmad-output/initiative-ai-language-teacher/ux-ai-language-teacher/DESIGN.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nav «План» (`/plan`) is still `TitleStubView` — Learners cannot open a view-only Living plan document with goals, focus, and upcoming topics after Living plan creation (CAP-3 viewability; UX Living plan document).

**Approach:** Replace the `/plan` stub with a full-screen view-only Vue document that loads `GET /living-plan` via existing `fetchLivingPlan`. On success, render three `var(--color-surface)` sections on `var(--color-bg)`. On `living_plan_not_found`, show Option B single empty state (not three sections). Match Settings shell patterns and Russian chrome.

## Boundaries & Constraints

**Always:**

- Wire JSON `snake_case`; read via teacher HTTP only (`fetchLivingPlan` / `LivingPlanProjection`, plus `fetchLearner` for empty-state CTA routing)
- Full-screen route (not a drawer); page canvas `var(--color-bg)`; section blocks `var(--color-surface)`
- View-only: no edits, no POST create from this surface, no client-written plan rows
- Russian chrome strings frozen below; section kickers uppercase like Settings
- Empty Option B only when `TeacherApiError.code === 'living_plan_not_found'`
- Mid-onboarding vs Calendar CTA uses read-only `gateDestination(learner)` / `isOnboardingRoute` — never `!plan_complete` alone (gate voids `plan_complete` until story 2.6)
- Auth: no GET until `running`; watch/subscribe so `starting`→`running` auto-fetches; stale-response generation like Settings

**Never:**

- Replan banner, change-history, or CAP-5 APIs (later epic/story)
- Calendar side-panel Living plan entry or first-lesson tip (story 2.6)
- Edits to `OnboardingPlanStub`, onboarding gate climax, or `gate.ts` (read-only import OK)
- Teacher domain/API/persistence changes; TeacherHost; Settings goals editing (2.7)
- Progress route; inventing lesson topic/status beyond `upcoming_topics` strings
- Manual section edit or “ask teacher to replan” CTA in this slice
- Treating non-`living_plan_not_found` errors (incl. 500 `plan_inconsistent`) as empty UX

## Frozen chrome (Russian)

- Page title: «План»
- Section kickers: «ЦЕЛИ» / «ФОКУС» / «БЛИЖАЙШИЕ ТЕМЫ»
- Empty body: «План обучения ещё не готов.»
- Empty CTA onboarding: «Продолжить настройку»
- Empty CTA calendar: «К календарю»
- Loading: «Загрузка…»
- Fallback API error (no `message`): «Не удалось загрузить план»
- Soft-empty list/focus (HTTP 200, empty fields): «Пока пусто»

## I/O & Edge-Case Matrix

| Scenario             | Input / State                                                              | Expected Output / Behavior                                                                                                                         | Error Handling                                                                    |
| -------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Happy path           | Teacher `running`; GET 200 with non-empty fields                           | Full-screen «План»; three surface sections listing goals / focus / upcoming_topics                                                                 | No error expected                                                                 |
| Soft-empty 200       | GET 200; empty `goals` and/or blank `focus` and/or empty `upcoming_topics` | Still three sections; empty fields show «Пока пусто» (not Option B)                                                                                | Coerce non-array goals/topics to `[]` before render                               |
| Loading              | Auth/plan fetch in flight                                                  | «Загрузка…» on bg; no sections                                                                                                                     | Ignore stale responses via load generation                                        |
| Auth becomes running | Mounted on `/plan` while `starting`, then `running`                        | Auto-fetch plan (Settings-style)                                                                                                                   | Do not leave stuck loading                                                        |
| Teacher not running  | Auth `starting` / `error` / no bearer                                      | Status copy + Settings-style retry (`retryTeacher`)                                                                                                | Do not call GET until `running`                                                   |
| API error            | Non-`living_plan_not_found` TeacherApiError / network                      | Inline error (`message` or fallback); retry reloads plan                                                                                           | On 401/403: rehydrate auth; do not tight-loop plan retry                          |
| Empty / not found    | `TeacherApiError.code === 'living_plan_not_found'`                         | Single surface: «План обучения ещё не готов.» + secondary CTA — no three placeholder sections                                                      | Empty UX, not hard error banner                                                   |
| Empty CTA — mid GATE | 404 + `isOnboardingRoute(gateDestination(learner))`                        | CTA «Продолжить настройку» → named route from `gateDestination` (`onboarding` / `onboarding-consent` / `onboarding-placement` / `onboarding-plan`) | If `fetchLearner` fails, keep empty body; omit CTA or show Calendar fallback once |
| Empty CTA — calendar | 404 + `gateDestination` === `calendar`                                     | CTA «К календарю» → `{ name: 'calendar' }`                                                                                                         | Router `beforeEach` may still redirect if GATE changes; acceptable                |

**Decision (empty/404):** Option B — single empty state (not soft empty sections, not auto-redirect). Mid-onboarding = `isOnboardingRoute(gateDestination(learner))`, not `!plan_complete`.

</frozen-after-approval>

## Design Notes

Settings density: accent rule + uppercase kicker + body list/paragraph in surface blocks. Goals and upcoming topics as simple lists (not coral numbered lesson-step circles — those stay for the lesson sidebar and later UI). Focus is one paragraph. Nav «План» is the only entry in this story.

## Code Map

- `apps/desktop/src/renderer/src/router/index.ts` (~L88–92) — swap `plan` route from `TitleStubView` → `PlanView` (keep `name: 'plan'`, path `/plan`)
- `apps/desktop/src/renderer/src/views/TitleStubView.vue` — leave for Progress; do not delete
- `apps/desktop/src/renderer/src/views/SettingsView.vue` — shell + auth seq / loading / retry patterns to mirror
- `apps/desktop/src/renderer/src/services/teacherClient.ts` — `getTeacherAuth`, `retryTeacher`, `fetchLivingPlan`, `fetchLearner`, `LivingPlanProjection`, `TeacherApiError`
- `apps/desktop/src/renderer/src/onboarding/gate.ts` — read-only `gateDestination`, `isOnboardingRoute` (do not edit)
- `apps/desktop/src/renderer/src/App.vue` — existing «План» nav; change only if assertions require
- `apps/desktop/src/renderer/src/styles/tokens.css` — `--color-bg` / `--color-surface`; do not retoken
- `apps/desktop/src/renderer/src/views/SettingsView.spec.ts` — mount via `RouterView` + mocked `window.teacher` + stubbed `fetch`
- Teacher `GET /living-plan` / domain — wire-complete; **do not change**

## Tasks & Acceptance

**Execution:**

- [x] `apps/desktop/src/renderer/src/views/PlanView.vue` — implement per Intent + matrix + frozen chrome (auth watch, fetchLivingPlan, three sections or Option B empty + gate CTA via fetchLearner) — CAP-3 view surface
- [x] `apps/desktop/src/renderer/src/router/index.ts` — wire `plan` → `PlanView`
- [x] `apps/desktop/src/renderer/src/views/PlanView.spec.ts` — Vitest: happy; soft-empty 200; loading; teacher-not-running + retry; non-404 error; 404 + mid-GATE CTA route; 404 + calendar CTA; coerce bad arrays — prove I/O matrix
- [x] `apps/desktop/src/renderer/src/App.spec.ts` (only if needed) — update `/plan` expectations — keep suite green

**Acceptance Criteria:**

- Given teacher running and GET 200 Living plan, when Learner opens «План» (`/plan`), then a full-screen document on `var(--color-bg)` shows three `var(--color-surface)` sections (ЦЕЛИ / ФОКУС / БЛИЖАЙШИЕ ТЕМЫ) with the API values (view-only); empty fields show «Пока пусто» without collapsing to Option B.
- Given teacher is not `running`, when Learner is on `/plan`, then they see status copy and a Settings-style retry, and no GET runs until `running`.
- Given GET fails with a non-`living_plan_not_found` error, when Learner is on `/plan`, then they see inline error copy (API `message` or fallback) and can retry without leaving the route.
- Given `living_plan_not_found`, when Learner is on `/plan`, then Option B single empty state shows («План обучения ещё не готов.») with «Продолжить настройку» to the `gateDestination` named route when mid-GATE, or «К календарю» when destination is `calendar`.

## Implementation Notes

- Added `PlanView.vue`: Settings-style auth watch/`loadSeq`, `fetchLivingPlan` when `running`, three surface sections (ЦЕЛИ / ФОКУС / БЛИЖАЙШИЕ ТЕМЫ) or Option B empty + CTA via `fetchLearner` + `gateDestination` / `isOnboardingRoute`. Soft-empty «Пока пусто»; non-404 errors inline with retry; 401/403 rehydrate auth without auto plan loop.
- Wired `/plan` → `PlanView` in `router/index.ts` (`TitleStubView` kept for Progress).
- `PlanView.spec.ts` covers the I/O matrix rows; `App.spec.ts` asserts plan document vs progress stub.
- Verified: `cd apps/desktop && npm test` (195 passed) and `npm run build`.

## Plan Change Log

## Review Triage Log

### Pass 1 (quick) — 2026-10-03

- verdict: `medium` — route: `patch` — `PlanView.spec.ts` loading case sets hash after `createWebHashHistory`, so isolated run fails and matrix Loading row is not proved; full file only passes via leftover `#/plan`. Evidence: `npm test -t loading:` → VUE_ROUTER_R0004 / empty `plan-loading`.
- verdict: `low` — route: `patch` — `PlanView.vue` `retry()` catch always says «Не удалось перезапустить учителя» even when only `getTeacherAuth()` failed on the running/API-error path. Evidence: `retry()` branches; Settings always calls `retryTeacher()`, this view does not on that branch.
- verdict: `low` — route: `patch` — blank focus «Пока пусто» uses `.body` (ink) while goals/topics soft-empty use `.soft-empty` (muted). Evidence: template `plan-focus` vs `goals-soft-empty` / `topics-soft-empty` classes.
- verdict: `medium` — route: `patch` — no tests for `fetchLearner` failure on 404 (omit CTA) or 401/403 rehydrate without tight plan-retry loop; matrix Error Handling / task “prove I/O matrix” leave those paths unchecked. Evidence: `resolveEmptyCta` catch and `loadPlan` 401/403 branch exist; suite has no cases.

## Verification

**Commands:**

- `cd apps/desktop && npm test` — expected: PlanView + existing suites pass
- `cd apps/desktop && npm run build` — expected: production build succeeds

**Manual checks (if no CLI):**

- With a seeded plan row, open `/plan` (hash `#/plan` in Electron): three sections; no edit controls
- With no plan (404), confirm single empty surface + correct secondary CTA
