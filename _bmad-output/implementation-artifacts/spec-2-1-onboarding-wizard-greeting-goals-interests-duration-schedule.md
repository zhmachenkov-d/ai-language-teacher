---
title: "2.1 Onboarding wizard — greeting, goals, interests, duration, schedule"
type: "feature"
created: "2026-09-28"
status: "done"
route: "dispatch"
review_loop_iteration: 0
baseline_commit: "bb5041a14a33ce7ac741cf14cab7e24fb2c3ebaf"
context:
  - "{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** First launch opens the empty calendar — Learners cannot complete FR1 intake (`address_as` / how to address, age, goals, interests/emphasis, duration, weekly schedule), so Living plan and reminders have nothing durable to read.

**Approach:** Ship a first-run Russian wizard (greeting → goals/outcome → interests/emphasis → duration → compact weekly slot list) that persists each step via authenticated `GET`/`PATCH /learner`, gates unfinished intake and pre-consent states off calendar-as-done, and hands off to a stub consent route for 2.2. Outlook week-grid chrome is deferred.

**Decisions:**

- RESUME: reopen mid-wizard at the next incomplete step; hydrate prior fields from `GET /learner`
- PREF_INPUT: multi-select Russian chips + optional «Другое»; advance needs ≥1 chip **or** non-empty Другое per group (Другое alone is enough)
- HANDOFF: after schedule save → stub `#/onboarding/consent`; do not open calendar as onboarded
- GATE: intake incomplete → wizard/RESUME; intake complete + consent not done → consent stub; calendar only after later climax (2.6) — never `/` → calendar while gated
- TIMEZONE: auto-detect via `Intl` on schedule step; read-only confirmation; persist on Learner
- SCHEDULE_UI: compact add/remove rows (weekday + local start); same slot model as future Outlook grid; ≥1 slot required
- WEEKDAY: ISO `0=Monday … 6=Sunday`; `start_minute` 0–1439 local to learner timezone
- STEP_COMPLETE: greeting = non-empty `address_as` + integer age 1–120 (age&lt;16 stored; hard-block UI is 2.2); each pref group per PREF_INPUT; duration ∈ {30,45,60}; schedule = ≥1 slot + timezone. Advance `intake_step` only after successful PATCH
- API: `GET /learner` + `PATCH /learner` snake_case body may include `address_as`, `age`, `goals`, `desired_outcome`, `interests`, `emphasis`, `lesson_duration_minutes`, `timezone`, `weekly_slots`, `intake_step` (plus existing `id`/`target_language`/`l1` on GET)
- PREF_CHIPS (starter): goals — «Работа / карьера», «Путешествия», «Учёба», «Повседневное общение»; outcome — «Уверенный разговор», «Понимать на слух», «Письмо / почта», «Собеседования»; interests — «Технологии», «Новости», «Фильмы», «Повседневность»; emphasis — «Говорение», «Аудирование», «Словарь», «Грамматика»

## Boundaries & Constraints

**Always:**

- One screen = one step on `--color-bg` with `--color-surface` sections; primary coral «Далее»
- Persist via domain → PersistencePort/SQLite; Vue uses Bearer loopback only; errors `{code,message,retryable}`
- Age only on greeting; under-16 hard-block is 2.2
- Schedule ≥1 slot + `timezone` (AD-13); `target_language`/`l1` stay `en`/`ru` (AD-10)
- Reuse AUTH_BRIDGE (`teacherClient`) and tokens; Russian strings hardcoded
- Opaque UUID learner id; no `onboarding_complete` in 2.1 (climax is 2.6)
- Apply GATE on every cold start / navigation to `/` or calendar

**Never:**

- Outlook week-grid chrome (deferred); Settings Goals/Schedule persist (2.7); real consent/placement/plan (2.2–2.4)
- Under-16 exit UI; surname/postal/email/phone fields; LLM-bound prompts (including `address_as`)
- SQLite from Vue; IPC as domain bus; TeacherHost/tray/HOST_SURVIVAL changes
- Autosave-on-keystroke; silent success when teacher is down; calendar-as-onboarded after intake alone

## I/O & Edge-Case Matrix

| Scenario                     | Input / State                      | Expected Output / Behavior                                       | Error Handling                         |
| ---------------------------- | ---------------------------------- | ---------------------------------------------------------------- | -------------------------------------- |
| First launch                 | Intake incomplete                  | Wizard at greeting or RESUME step                                | N/A                                    |
| Greeting                     | Valid `address_as` + age + «Далее» | PATCH; advance                                                   | Reject blank/`address_as` or age∉1–120 |
| Prefs / duration             | STEP_COMPLETE + «Далее»            | PATCH; advance                                                   | Error + retry if teacher down          |
| Schedule zero                | No slots + «Далее»                 | Blocked; clear RU copy                                           | Stay                                   |
| Schedule OK                  | ≥1 slot + timezone + «Далее»       | Persist; stub consent route                                      | Error + retry                          |
| Mid-wizard reopen            | Partial saves                      | Next incomplete step; hydrated                                   | N/A                                    |
| Intake done, consent pending | Reopen app / hit `/` or calendar   | Stub `#/onboarding/consent` — not calendar, not restart greeting | N/A                                    |
| Auth / down                  | 401 or unreachable on save         | No local-only success                                            | Surface `{code,message,retryable}`     |

</frozen-after-approval>

## Code Map

- `epic-2-context.md` / `epics.md` Story 2.1 — AC + pipeline
- `deferred-work.md` — Outlook grid split; on Done annotate 1.3 learner HTTP as **partial** `resolved_by` (intake subset only)
- `spec-1-6-…` — AUTH_BRIDGE / `teacherClient`; Settings stubs stay
- `domain/learner.py` + `ports/persistence.py` + `adapters/persistence/sqlite.py` — extend Learner; update use case; slots JSON
- `adapters/api/app.py` — DI store; `GET`/`PATCH /learner`; Bearer + envelopes
- `tests/` — persistence + API I/O matrix
- `router/index.ts` + `App.vue` — `/onboarding`, stub consent, GATE; hide nav in wizard/consent
- New `OnboardingWizard.vue` (+ steps) — five steps; compact slot list
- `teacherClient.ts` — `GET`/`PATCH /learner`
- Do not change `main/` / `preload/` / `TeacherHost` / `SettingsView` persist

## Tasks & Acceptance

**Execution:**

- [x] `domain/learner.py` + persistence port/adapter — intake fields, `intake_step`, slots JSON, update use case
- [x] `adapters/api/app.py` + tests — `GET`/`PATCH /learner`; wire store; I/O matrix
- [x] `teacherClient.ts` — learner GET/PATCH via AUTH_BRIDGE
- [x] `OnboardingWizard.vue` (+ steps) — greeting→…→slot list; chips+Другое; coral «Далее»
- [x] `router/index.ts` + `App.vue` — GATE + RESUME + stub consent HANDOFF
- [x] Renderer specs — gate, persist, zero-slot, mid-wizard + post-intake reopen
- [x] `uv run pytest` + `npm test` + `npm run build`
- [x] On Done: sprint-status 2-1 → review; deferred-work intake HTTP partial `resolved_by`

**Acceptance Criteria:**

- Given first launch with incomplete intake, when the app opens, then the wizard starts (not calendar-as-onboarded)
- Given each intake step, when «Далее» with STEP_COMPLETE input, then values persist via `PATCH /learner` and the next step (or stub consent) shows
- Given schedule with zero slots, when «Далее», then advance is blocked with clear Russian copy
- Given mid-wizard exit with partial saves, when the app reopens, then it resumes at the next incomplete step with hydrated fields
- Given intake complete and consent not done, when the app reopens or navigates to `/`/calendar, then stub consent shows — not calendar-as-onboarded
- Given teacher down or 401 on save, when «Далее», then there is no silent local-only success

## Implementation Notes

- Pref lists: JSON arrays of selected chip labels plus optional free-text «Другое» string in the same list (no separate `_other` columns).
- Duplicate weekly slots: coalesced on PATCH by `(weekday, start_minute)` (first-seen order).
- Completing intake (`intake_step=complete`) is rejected server-side when `weekly_slots` is empty.
- `intake_step` values: `greeting` → `goals` → `interests` → `duration` → `schedule` → `complete`. Advance only after successful PATCH.
- GATE: `/` and calendar redirect to wizard while `intake_step !== complete`, else consent stub. Calendar climax remains 2.6 — no `onboarding_complete` flag in 2.1.
- `create_app` wires `SqliteStore(config.sqlite_path())` on `app.state.store`; `GET /learner` get-or-creates; `/health` still does not require a row.
- SQLite migrates legacy learner tables via `ALTER TABLE … ADD COLUMN` for intake fields.
- Router exposes `setGateLearnerOverride` for Vitest only.
- Verified 2026-09-28: `uv run pytest` 72 passed; `npm test` 97 passed; `npm run build` green. Review patches applied (HH:MM:SS parse, complete STEP_COMPLETE server checks, corrupt slot load harden, consent null→wizard, GATE/wizard test gaps).

## Spec Change Log

## Review Triage Log

- blind: `parseStartMinute` rejects `HH:MM:SS` from `<input type="time">` — **medium** — regex is `^(\d{1,2}):(\d{2})$` only; browsers can emit seconds → add-slot fails. Route: patch
- blind: `PATCH /learner` does not enforce full STEP_COMPLETE when setting `intake_step=complete` (beyond slots) — **medium** — confirmed; only empty-slots rejected. Route: patch (group with edge complete-fields)
- blind: no test for legacy `ALTER TABLE` intake migration — **medium** — verified; fresh DBs only. Route: patch (group with VG migration)
- blind: no «Назад» in wizard — **false** — frozen intent never requires back navigation
- blind: `gateDestination(complete)` always consent; no calendar unlock — **false** — intentional for 2.1; climax is 2.6
- blind: GATE treats teacher `starting` like unavailable → wizard flash — **low** — matches fail-toward-wizard; wait/retry would add host complexity beyond this story. Rejected (low + non-trivial)
- blind: English API error strings in Russian wizard — **low** — server unauthorized message is English; unlikely everyday after auth works. Rejected (low)
- blind: `splitPrefList` keeps only first non-chip «Другое» — **false** — UI/`mergePrefList` only ever writes one other string
- blind: `nav-hidden` class unused while `v-if` hides nav — **low** — dead class on `App.vue`. Route: patch
- blind: wizard specs skip interests/duration/Другое-alone — **medium** — confirmed. Route: patch (group with VG mid-wizard PATCH)
- blind: “ISO weekday 0=Monday” naming inaccurate vs ISO 8601 — **false** — frozen WEEKDAY decision defines the project convention
- blind: Plan/Progress ungated while intake incomplete — **false** — frozen GATE only covers `/` and calendar; nav hidden on wizard/consent
- blind: empty Spec Change Log / Triage while status review — **false** — process placeholders filled by this review step
- blind: unused `intakeIncomplete` export — **low** — confirmed unused. Route: patch
- blind: hydrate treats stored `"UTC"` as unset and re-detects — **false** — TIMEZONE=A auto-detect; default pre-schedule timezone is UTC; wizard only persists timezone on schedule complete
- edge: `_loads_slots` KeyError when slot JSON lacks keys — **high** — `item["weekday"]` unguarded. Route: patch (group corrupt load)
- edge: `_loads_*` JSONDecodeError on corrupt text — **medium** — bare `json.loads`. Route: patch (group corrupt load)
- edge: out-of-range slots loaded without validate — **medium** — no `validate_weekly_slot` on load. Route: patch (group corrupt load)
- edge: `#/onboarding/consent` with `learner==null` stays on consent — **medium** — `return true` when null. Route: patch
- edge: `intake_step=complete` without greeting/prefs/duration — **medium** — same root as blind STEP_COMPLETE. Route: patch
- edge: `parseStartMinute` HH:MM:SS — **medium** — same as blind time parse. Route: patch
- edge: bool `True`/`False` accepted as weekday/start_minute — **medium** — `isinstance(True, int)`. Route: patch
- edge: multi-«Другое» hydrate loss — **false** — same as blind splitPrefList
- edge: double «Далее» before `saving` disables — **low** — button `:disabled="saving"` but no early return. Route: patch (trivial guard)
- verification-gap: pre-2.1 SQLite migration untested — **medium** — pre-verified. Route: patch
- verification-gap: GATE production `fetchLearner` path skipped by override — **medium** — pre-verified. Route: patch
- verification-gap: incomplete learner on consent route untested — **medium** — pre-verified. Route: patch
- verification-gap: goals/interests/duration PATCH paths untested — **medium** — pre-verified. Route: patch
- verification-gap: schedule-save test omits PATCH body assert — **medium** — pre-verified. Route: patch

## Design Notes

- Pref list fields store selected chip labels plus optional Другое string (shape agent-owned; keep PATCH snake_case).
- `create_app` gains PersistencePort from `config.sqlite_path`; `get_or_create` on first learner call so CLI `/health` needs no pre-existing row.
- Keep slot-list UI extractable for deferred Outlook grid / 2.7 Settings mini-wizard.
- Duplicate slot rows: reject or coalesce on PATCH (agent choice; record in Implementation Notes).

## Verification

**Commands:**

- `cd services/teacher && uv run pytest` — green including `/learner` tests
- `cd apps/desktop && npm test && npm run build` — Vitest + build green

**Manual checks:**

- Cold start → wizard; finish schedule → stub consent; reopen → consent stub; mid-wizard kill/reopen → RESUME; `/` never shows finished onboarding early
