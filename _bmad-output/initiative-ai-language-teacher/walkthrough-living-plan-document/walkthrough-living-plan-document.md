# Walkthrough: Living plan full-screen document (view-only)

Target: branch `feat/2-5-living-plan-document` (commit `5591a85`), guided by [story plan](../epic-first-run-onboarding-living-plan-on-calendar/story-living-plan-full-screen-document-view-only-plan.md).

Current block: none — review wrapped up

## Blocks

- [x] **1 — Intent** — done
- [x] **2 — Broad strokes** — done
- [x] **3 — Auth watch and load sequence** — done
- [x] **4 — Three-section document (happy + soft-empty)** — done
- [x] **5 — Option B empty state and CTA** — done
- [x] **6 — Errors and retry** — done
- [x] **7 — Periphery** — done

Changed during review: none yet.

---

## 1 — Intent

Status: done

Source: frozen Intent from the [story plan](../epic-first-run-onboarding-living-plan-on-calendar/story-living-plan-full-screen-document-view-only-plan.md) (verbatim).

**Problem:** Nav «План» (`/plan`) is still `TitleStubView` — Learners cannot open a view-only Living plan document with goals, focus, and upcoming topics after Living plan creation (CAP-3 viewability; UX Living plan document).

**Approach:** Replace the `/plan` stub with a full-screen view-only Vue document that loads `GET /living-plan` via existing `fetchLivingPlan`. On success, render three `var(--color-surface)` sections on `var(--color-bg)`. On `living_plan_not_found`, show Option B single empty state (not three sections). Match Settings shell patterns and Russian chrome.

---

## 2 — Broad strokes

Status: done

What changed: a new full-screen Plan view is wired to `/plan`; it reads Living plan over teacher HTTP and renders view-only sections or a single empty state. Teacher domain/API untouched.

Open these first:

1. [router/index.ts:89](../../../apps/desktop/src/renderer/src/router/index.ts#L89) — `plan` route now mounts `PlanView` (Progress still uses `TitleStubView`).
2. [PlanView.vue](../../../apps/desktop/src/renderer/src/views/PlanView.vue) — the document surface: auth watch, fetch, three sections or Option B.
3. [teacherClient.ts](../../../apps/desktop/src/renderer/src/services/teacherClient.ts) — existing `fetchLivingPlan` / `fetchLearner` / auth helpers (read, not rewritten).
4. [gate.ts](../../../apps/desktop/src/renderer/src/onboarding/gate.ts) — read-only `gateDestination` / `isOnboardingRoute` for empty CTA routing.
5. [PlanView.spec.ts](../../../apps/desktop/src/renderer/src/views/PlanView.spec.ts) — Vitest coverage of the I/O matrix.

---

## 3 — Auth watch and load sequence

Status: done

Mechanism: On mount, PlanView hydrates teacher auth and only calls `fetchLivingPlan` when status is `running`. A load-generation counter drops stale responses. If auth is still `starting`, a watch/subscribe path re-runs when it becomes `running` (Settings-style). Until then the UI shows loading or teacher status + retry, not plan sections.

Places:

- [PlanView.vue:58](../../../apps/desktop/src/renderer/src/views/PlanView.vue#L58) — `applyAuth` gates on generation.
- [PlanView.vue:135](../../../apps/desktop/src/renderer/src/views/PlanView.vue#L135) — `refreshStatus` / initial hydrate.
- [PlanView.vue:206](../../../apps/desktop/src/renderer/src/views/PlanView.vue#L206) — `onMounted` + watch when auth becomes `running`.
- Pattern source: [SettingsView.vue](../../../apps/desktop/src/renderer/src/views/SettingsView.vue).

---

## 4 — Three-section document (happy + soft-empty)

Status: done

Mechanism: A 200 Living plan projection paints three surface blocks — ЦЕЛИ, ФОКУС, БЛИЖАЙШИЕ ТЕМЫ — on the page background. Empty arrays or blank focus stay as three sections with «Пока пусто»; that is soft-empty, not Option B. Non-array goals/topics are coerced to `[]` before render. View-only: no edit controls, no POST.

Places:

- [PlanView.vue:87](../../../apps/desktop/src/renderer/src/views/PlanView.vue#L87) — `loadPlan` success path sets `plan`.
- [PlanView.vue:39](../../../apps/desktop/src/renderer/src/views/PlanView.vue#L39) — `goals` / `focusText` / `upcomingTopics` computed + soft-empty coercion.
- Template sections in [PlanView.vue](../../../apps/desktop/src/renderer/src/views/PlanView.vue) (kickers + lists).

---

## 5 — Option B empty state and CTA

Status: done

Mechanism: Only `TeacherApiError.code === 'living_plan_not_found'` collapses to a single empty surface («План обучения ещё не готов.»). CTA label/route comes from `fetchLearner` + `gateDestination`: mid-onboarding routes get «Продолжить настройку»; calendar gets «К календарю». Mid-GATE is `isOnboardingRoute(gateDestination(learner))`, not `!plan_complete`. If learner fetch fails, empty body can omit CTA.

Places:

- [PlanView.vue:108](../../../apps/desktop/src/renderer/src/views/PlanView.vue#L108) — 404 / `living_plan_not_found` branch.
- [PlanView.vue:66](../../../apps/desktop/src/renderer/src/views/PlanView.vue#L66) — `resolveEmptyCta`.
- [gate.ts](../../../apps/desktop/src/renderer/src/onboarding/gate.ts) — destination helpers (unchanged).

---

## 6 — Errors and retry

Status: done

Mechanism: Non-404 API/network failures show inline error (`message` or «Не удалось загрузить план») with retry that reloads the plan when already `running`. Teacher not running shows status copy and Settings-style `retryTeacher`. On 401/403, auth is rehydrated without a tight plan-retry loop.

Places:

- [PlanView.vue:87](../../../apps/desktop/src/renderer/src/views/PlanView.vue#L87) — error branches in `loadPlan`.
- [PlanView.vue:161](../../../apps/desktop/src/renderer/src/views/PlanView.vue#L161) — `retry()`.

---

## 7 — Periphery

Status: done

- [App.spec.ts:334](../../../apps/desktop/src/renderer/src/App.spec.ts#L334) — asserts `/plan` shows plan document (not calendar panel); Progress remains stub.
- [story plan](../epic-first-run-onboarding-living-plan-on-calendar/story-living-plan-full-screen-document-view-only-plan.md) — ticket contract, frozen chrome, prior quick-review triage notes.
- Verification noted in plan: `cd apps/desktop && npm test` / `npm run build`.
