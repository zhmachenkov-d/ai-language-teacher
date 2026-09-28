---
title: "2.2 Consent and regulated copy gating"
type: "feature"
created: "2026-09-28"
status: "done"
route: "dispatch"
review_loop_iteration: 0
baseline_commit: "50e93c13134fe6f99826b88b935eb68def1a13ce"
context:
  - "{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After intake, Learners land on a consent stub with no mic/Telegram consent, AI/Privacy disclaimers, or age&lt;16 hard-block — so placement cannot lawfully start and Privacy/PII policy is not gated (FR1 handoff, UX-DR20, NFR1).

**Approach:** Replace the consent stub with a real Russian consent step that persists required acknowledgements via `GET`/`PATCH /learner`, hard-blocks under-16 with a regulated exit, keeps calendar gated until 2.6, and hands off to a placement stub for 2.3.

**Decisions:**

- TELEGRAM: OPTIONAL — step **includes** Telegram consent copy/checkbox (Epic AC), but Telegram is **not** required to proceed; mic + AI + Privacy are required; decline persists `consent_telegram=false` and is re-prompted at Settings «Привязать» in 4.1
- AGE_EXIT: QUIT_IPC — under-16 hard-block + «Закрыть приложение» → thin `desktop:quit` IPC (main sets same `isQuitting` path as tray «Выход» + `app.quit()`); lifecycle-only, no domain bus
- HANDOFF: PLACEMENT_STUB — after successful consent PATCH → `#/onboarding/placement` chrome-only stub for 2.3
- COPY: AGENT_DRAFT — implementer writes plain Russian covering: mic/voice + persistent storage for replay; Telegram; AI not certified teacher / not exam guarantee; Privacy/PII (no surname/postal/email/phone to LLM); no certificate/level/exam-pass claims — reviewable in PR
- CONSENT_COMPLETE: FLAG — explicit `consent_complete: bool` (default false); «Далее» PATCH sets it true only with required flags + age≥16; GATE reads this flag (not derived-only)

## Boundaries & Constraints

**Always:**

- Age from greeting only — never re-ask on consent; age&lt;16 (or age null) hard-blocks (no minor/limited mode)
- Explicit mic/voice (incl. persistent storage for replay), Telegram, AI disclaimer, Privacy/PII; plain Russian; no certificate/level/exam-pass claims
- Required for `consent_complete=true`: `consent_mic`, `consent_ai`, `consent_privacy`, age≥16 — Telegram optional
- Persist via teacher domain/API (`snake_case`); UI commands only
- GATE order: intake incomplete → wizard; intake complete && !consent_complete → consent; consent_complete → placement stub; calendar only after 2.6
- Wire errors `{ code, message, retryable }`; Bearer loopback; fail closed toward wizard/consent — never calendar-as-onboarded
- QUIT_IPC allowed: shared channel + preload `desktop.quit` + main handler mirroring tray quit (`isQuitting=true`, `app.quit()`)

**Never:**

- Placement briefing/tasks, Living plan, or calendar climax (placement stub = chrome/copy only)
- OS mic permission prompt / Voice capture (2.3+); Telegram deep-link (4.1)
- Re-collect age; invent limited under-16 mode
- Change TeacherHost spawn/attach/health or Settings LLM persist; proxy domain via Electron main
- Send surname/postal/email/phone into LLM context

## I/O & Edge-Case Matrix

| Scenario               | Input / State                                                    | Expected Output / Behavior                                                           | Error Handling                            |
| ---------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------- |
| Happy path             | intake complete; age≥16; mic+AI+Privacy checked; «Далее»         | PATCH sets consents + `consent_complete=true` (Telegram as chosen); → placement stub | Teacher/401: no silent local-only success |
| Under-16               | intake complete; age&lt;16                                       | Hard-block + «Закрыть приложение» → `desktop:quit`; no placement                     | N/A                                       |
| Missing required (UI)  | age≥16; mic/AI/Privacy unchecked; «Далее»                        | Stay on consent; clear Russian block copy; no PATCH complete                         | N/A                                       |
| Invalid complete (API) | PATCH `consent_complete=true` with age&lt;16 or missing required | 422 `{ code, message, retryable }` — complete rejected                               | Client shows error; stay on consent       |
| Telegram decline       | age≥16; required checked; Telegram unchecked; «Далее»            | Persist `consent_telegram=false`, `consent_complete=true`; → placement stub          | N/A                                       |
| Reopen mid-consent     | intake complete; `consent_complete=false`                        | Resume consent (not wizard/calendar)                                                 | null learner → fail closed to wizard      |
| Reopen post-consent    | `consent_complete=true`                                          | Placement stub (not calendar)                                                        | null on placement → fail closed to wizard |
| Age missing            | intake complete; age null                                        | Hard-block + quit CTA (same as under-16)                                             | API rejects `consent_complete=true`       |

</frozen-after-approval>

## Code Map

- `epic-2-context.md` / `epics.md` Story 2.2 — AC; consent topics
- `spec-2-1-…` — GATE/RESUME/HANDOFF; age&lt;16 stored; stub consent
- `onboarding/gate.ts` — read `intake_step` + `consent_complete`; destinations: wizard | consent | placement (| calendar unused until 2.6)
- `router/index.ts` — real consent view; placement stub route; resume among wizard/consent/placement
- Consent view — replace `OnboardingConsentStub.vue` (or new file + route swap)
- Placement stub view — chrome-only handoff for 2.3
- `domain/learner.py` + `sqlite.py` + persistence port — four consent bools + `consent_complete`; ALTER migrate; reject invalid complete
- `adapters/api/app.py` + `tests/test_learner_api.py` — GET/PATCH; 422 matrix for under-16 / missing required complete
- `teacherClient.ts` — mirror fields
- `shared/ipcChannels.ts` + `preload/index.ts` + `preload/index.d.ts` + `main/index.ts` — `desktop:quit` (same `isQuitting` as tray); Vitest for channel exposure / handler wiring
- `App.spec.ts` (+ consent specs) — gate, under-16 quit CTA mock, required block, persist, reopen
- Do not change TeacherHost spawn/attach/health logic or Settings LLM persist

## Tasks & Acceptance

**Execution:**

- [x] `domain/learner.py` + persistence — `consent_mic|telegram|ai|privacy` + `consent_complete`; server rejects `consent_complete=true` unless required+age≥16; ALTER migrate
- [x] `adapters/api/app.py` + tests — GET/PATCH; 422 I/O for under-16 / missing required complete
- [x] `teacherClient.ts` — mirror consent fields
- [x] `ipcChannels` + preload + main — `desktop:quit` mirrors tray quit; typed `desktop.quit()`; unit test
- [x] Consent view — checkboxes, AGENT_DRAFT Russian copy checklist, coral «Далее»; under-16 hard-block + quit CTA
- [x] `gate.ts` + `router/index.ts` — FLAG-based GATE; HANDOFF to placement stub
- [x] Placement stub view — chrome-only (no briefing/placement logic)
- [x] Renderer specs — gate, under-16, required block, persist, reopen, null-on-placement
- [x] `uv run pytest` + `npm test` + `npm run build`
- [x] On Done: sprint-status 2-2 → review

**Acceptance Criteria:**

- Given intake complete and age≥16, when consent shows, then mic/Telegram/AI/Privacy copy is explicit and age is not re-asked
- Given age&lt;16, when consent route opens, then hard-block + «Закрыть приложение» invokes quit IPC; placement does not run
- Given mic/AI/Privacy unchecked, when «Далее», then advance is blocked with clear Russian copy
- Given PATCH `consent_complete=true` with age&lt;16 or missing required, when API handles it, then 422 envelope — complete not stored
- Given required consents accepted (Telegram optional), when «Далее», then PATCH sets `consent_complete=true` and placement stub shows — not calendar
- Given reopen after `consent_complete=true`, when navigating `/` or calendar, then placement stub (not calendar-as-onboarded)

## Implementation Notes

- 2026-09-28: Domain `Learner` + SQLite ALTER for `consent_mic|telegram|ai|privacy` + `consent_complete` (defaults false). `consent_complete=true` rejected unless age≥16 and mic/AI/Privacy true; Telegram optional. Wire 422 codes `age_restricted` / `consent_incomplete` via `LearnerValidationError`.
- GATE reads `consent_complete` FLAG: incomplete intake → wizard; intake done && !consent → consent; consent done → `#/onboarding/placement` stub (calendar still gated until 2.6).
- Replaced consent stub with `OnboardingConsent.vue` (AGENT_DRAFT Russian copy: mic+replay storage, optional Telegram, AI disclaimer, Privacy/PII). Under-16/null age hard-block on same route + `desktop:quit` IPC (shared `beginExplicitQuit` with tray «Выход»).
- Verified: `uv run pytest` (78), `npm test` (119), `npm run build` green. Manual GUI smoke not run in this environment.
- Risk: Russian consent copy is implementer-drafted — legal/product review recommended in PR. OS mic permission / Voice / Telegram deep-link remain deferred (2.3 / 4.1).
- 2026-09-28 review patches: `consent_complete` also requires `intake_step=complete` (`consent_before_intake`); consent quit CTA surfaces Russian error if `desktop.quit` missing; `onNext` ignores overlap while saving; `load()` generation guard; age=16 + mid-consent hydrate + RESUME placement specs; main/preload quit-channel source wiring assert.

## Spec Change Log

## Review Triage Log

- blind: new files appear under wrong `src/renderer/...` paths in the patch — **false** — `git diff --no-index` from repo root; files live at `apps/desktop/src/renderer/...` and Vitest discovers them
- blind: sprint-status bumps without story artifact in the change set — **false** — `spec-2-2-…md` is untracked on the same branch alongside the status edit
- blind: domain `_require_consent_complete` does not require `intake_step=complete` — **medium** — confirmed; mid-intake PATCH can set complete then skip consent UI after intake finishes. Route: patch
- blind: App.spec “calendar and /” only mounts `#/calendar` — **false** — `#/` reopen covered by `consent_complete opens placement stub` (mountApp `#/`)
- blind: no test hydrates checkboxes from GET mid-consent — **medium** — confirmed absent. Route: patch
- blind: English 422 messages shown in Russian UI — **low** — same pattern as 2.1; rejected (low + everyday rare after auth works)
- blind: quit CTA silent no-op if `desktop.quit` missing — **medium** — optional chaining confirmed. Route: patch
- blind: `invoke` + `app.quit` Promise may not settle — **low** — `void` call; user never awaits. Rejected (low + non-trivial Electron contract change)
- blind: `MIN_AGE` / `MIN_CONSENT_AGE` duplicated — **low** — rejected (cosmetic drift risk; shared package is extra surface)
- blind: `_seed_intake_complete` ignores seed PATCH status — **low** — test helper only. Route: patch (trivial assert)
- blind: no API coverage for consent_complete while intake incomplete — **medium** — same root as domain intake gate. Route: patch (group)
- edge: quit CTA when desktop.quit undefined — **medium** — carried same as blind quit no-op. Route: patch
- edge: PATCH consent_complete while intake incomplete — **medium** — carried same as blind domain intake. Route: patch
- edge: GATE placement when consent_complete + under-16 — **false** — any update with `consent_complete` re-runs `_require_consent_complete`; age downgrade after complete is 422
- edge: load() redirects to placement before age hard-block — **false** — unreachable via API for under-16 + complete; ageRestricted path only when complete is false
- edge: overlapping load() from mount/retry — **medium** — no generation guard. Route: patch
- edge: double «Далее» before saving disables — **low** — no early `if (saving) return`. Route: patch
- verification-gap: desktop:quit wiring test only asserts channel string — **medium** — pre-verified. Route: patch
- verification-gap: onboarding-route RESUME to placement when consent_complete untested — **medium** — pre-verified. Route: patch
- verification-gap: age=16 consent boundary untested — **medium** — pre-verified. Route: patch
- verification-gap other: quit optional-chain no-op — **medium** — carried same as blind quit. Route: patch

## Design Notes

- Four consent booleans + explicit `consent_complete` FLAG (not derived-only) so GATE and 4.1 Telegram re-prompt stay unambiguous.
- Server enforces the same complete rules as UI (mirror intake `complete` rigor); prefer a stable `code` e.g. `consent_incomplete` / `age_restricted` in 422 body.
- Mic copy must mention persistent storage for lesson replay (Epic 3 cites 2.2).
- Under-16: blocked UI on the consent route (same route, different body).
- Quit IPC is host lifecycle only — must set `isQuitting` before `app.quit()` so window-close hide policy does not fight tray-first survival.
- Reuse OnboardingWizard surface/accent-rule chrome; one step = one screen.

## Verification

**Commands:**

- `cd services/teacher && uv run pytest` — learner consent + under-16 / incomplete-complete API cases green
- `cd apps/desktop && npm test && npm run build` — gate/consent/age/quit Vitest + build green

**Manual checks:**

- Finish intake age≥16 → consent → accept → placement stub; reopen → stub; age 15 → hard-block → quit; uncheck required → «Далее» blocked; `/` never calendar
