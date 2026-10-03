---
title: "2.4 Living plan creation and persistence"
type: "feature"
ticket: 4
status: "done"
created: "2026-09-29"
baseline_revision: "cbc522e4151b414e7fc7133239b9bdf959d203c7"
review_loop_iteration: 2
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After placement there is no Living plan or scheduled first lessons, so the first-run curriculum cannot exist before lesson one (FR3).

**Approach:** Teacher domain proposes/auto-selects a learning path via LLM, then atomically persists a revisable LivingPlan + WEEK_FILL LessonRecords and sets `plan_complete`. Expose `POST`/`GET /living-plan`. Desktop UI for creating/ready chrome is deferred — stub + gate stay until that follow-up.

**Decisions:**

- PATH: server proposes 2–3 paths, auto-selects the recommended one (exactly one `recommended`; else first forced); no client picker
- SCHEDULE_HORIZON: WEEK_FILL — per `weekly_slots` entry, earliest local `local_dt > now` in `[now, now+7d)`; IANA → UTC `scheduled_at`; empty/zero hits → `schedule_unusable` (no invent)
- SCHEDULE_CLOCK: injectable `now` (prod = real UTC; tests = fixture)
- POST_BODY: `POST /living-plan` `{}` → **200** LivingPlan projection; other bodies → 422; idempotent if plan exists (no re-LLM)
- DIFFICULTY: avg(listening, speaking) → `beginner`|[0,0.25) `elementary`|[0.25,0.5) `intermediate`|[0.5,0.75) `upper_intermediate`|[0.75,1]; missing scores → `placement_scores_missing`
- CURRICULUM: LLM validates to `goals: string[]`, `focus: string`, `upcoming_topics: string[]`; intake only in prompt
- PATHS_LLM: `{ id, title, summary, recommended }`; invalid count/schema → `llm_generation_failed`
- ATOMIC: one txn = LivingPlan + lessons + `plan_complete=true`; `UNIQUE(learner_id)`; GATE uses FLAG only — destination remains `onboarding-plan` until 2.6
- LESSON_WIRE: `{ id, scheduled_at, timezone }` only
- ERRORS: 422 `llm_config_missing` | `llm_generation_failed` | `placement_incomplete` | `placement_scores_missing` | `schedule_unusable`; GET !FLAG → 404 `living_plan_not_found`; FLAG w/o plan → 500 `plan_inconsistent`
- OUT_OF_SCOPE: desktop plan UI (UX-DR13); THREE+SERVER pause; LessonRecord status/topic; DST/IANA hardening — deferred-work

## Boundaries & Constraints

**Always:** Domain writes plan+lessons (AD-6/7); wire `snake_case`; errors `{ code, message, retryable }`; persist `goals`/`focus`/`upcoming_topics`/`difficulty`/`selected_path_id`/`proposed_paths`/`revisable=true`/`target_language="en"`/`l1="ru"` (AD-10); WEEK_FILL from intake slots+timezone (AD-13); never fake FLAG on LLM/schedule fail (NFR3 partial); NFR1 on prompts; project `plan_complete` on `GET /learner`.

**Never:** Plan document UI (2.5), calendar/onboarded (2.6), Settings Voice/Schedule product (2.7), LangGraph, lesson SSE, Telegram, TeacherHost/Settings-LLM rewrite, client-written plan rows, inventing times, Voice required, wall-clock WEEK_FILL tests, desktop creating/ready chrome, fail-count pause.

## I/O & Edge-Case Matrix

| Scenario             | Input / State                 | Expected Output                            | Error Handling                 |
| -------------------- | ----------------------------- | ------------------------------------------ | ------------------------------ |
| Ready create         | placement+Config+scores+slots | Atomic plan+WEEK_FILL+FLAG; 200 projection | N/A                            |
| Idempotent POST      | plan exists                   | Same projection; no re-LLM                 | N/A                            |
| Config missing       | no LLM Config                 | No rows                                    | 422 `llm_config_missing`       |
| LLM fail             | bad JSON / LLM / network      | No FLAG                                    | 422 `llm_generation_failed`    |
| No usable slots      | empty / zero WEEK_FILL        | No invent                                  | 422 `schedule_unusable`        |
| Slot past today      | fixture `now` after slot      | Omit if outside window                     | zero → `schedule_unusable`     |
| Placement incomplete | !placement_complete           | Reject                                     | 422 `placement_incomplete`     |
| Scores missing       | scores null                   | Reject                                     | 422 `placement_scores_missing` |
| GET resume           | FLAG + plan                   | 200 projection                             | N/A                            |
| GET no plan          | !FLAG                         | —                                          | 404 `living_plan_not_found`    |
| Inconsistent         | FLAG, no plan                 | —                                          | 500 `plan_inconsistent`        |

</frozen-after-approval>

## Code Map

- `epics.md` 2.4 — FR3; AD-6/7/10/13 (UI/pause ACs → deferred-work)
- `spec-2-3-…` — FLAG pattern; leave placement alone; reuse 422 shape
- `gate.ts` / `LearnerProfile` — add `plan_complete`; keep destination `onboarding-plan` (stub unchanged)
- `teacherClient.ts` — `plan_complete` + `createLivingPlan` / `fetchLivingPlan` types (no Vue view rewrite)
- NEW `domain/living_plan.py` — entities; `parse_path_options`; `seed_difficulty`; `week_fill_occurrences(*, now)`; `create_living_plan`
- `learner.py` + SQLite ALTER — `plan_complete`; require placement + scores
- PersistencePort + SQLite — `living_plan` `UNIQUE(learner_id)`; `lesson_record` (`id`, `living_plan_id`, `scheduled_at`, `timezone`); one txn
- `ports/llm.py` + adapter — `propose_learning_paths`; domain validates
- `adapters/api/app.py` — `POST`/`GET /living-plan`; project FLAG on `GET /learner`
- Wire: path + LivingPlan `{ id, goals, focus, upcoming_topics, difficulty, selected_path_id, proposed_paths, revisable, target_language, l1, lessons: [{ id, scheduled_at, timezone }] }`
- Do not change TeacherHost, Settings, CalendarHome, `/plan` TitleStub, `OnboardingPlanStub.vue` chrome

## Tasks & Acceptance

**Execution:**

- [x] `learner.py` + SQLite — `plan_complete`; project on `GET /learner`
- [x] `domain/living_plan.py` — bands; path/curriculum validate; WEEK_FILL(`now=`); atomic create
- [x] PersistencePort + SQLite — UNIQUE plan; lessons; atomic txn
- [x] LLM port/adapter + API POST/GET — error matrix; pytest (fixture `now`, idempotent, GET)
- [x] `teacherClient.ts` + `gate.ts` types/tests — `plan_complete` on profile; destination unchanged
- [x] `uv run pytest` + `npm test` + `npm run build`
- [x] On Done: sprint-status `2-4-…` → review

**Acceptance Criteria:**

- Given placement_complete, scores, LLM Config, and usable slots, when `POST /living-plan` `{}`, then LivingPlan+WEEK_FILL persist atomically with `plan_complete`, recommended path auto-selected, and 200 returns the projection
- Given LLM or schedule failure, when create is attempted, then the matching 422 is returned and `plan_complete` stays false
- Given an existing LivingPlan, when POST again, then the existing projection is returned with no re-LLM
- Given `plan_complete`, when `GET /living-plan`, then the projection is returned; without FLAG → 404; FLAG without row → 500

## Implementation Notes

## Spec Change Log

- 2026-09-29 split×2: main = teacher create API; deferred UI, THREE-pause, lesson richness, DST/IANA

## Review Triage Log

- review_loop 2: Split — four deferred goals; spec regenerated for API/domain only

### review_loop 3 (post-implement)

- blind: status in-review vs sprint review — verdict `false` — workflow: step-04 uses `in-review`; sprint `review` is the Done task state
- blind: empty Implementation Notes — verdict `false` — heading is optional; no user harm
- blind: AC omit POST_BODY non-`{}` — verdict `false` — rejected (would edit this build's AC/spec); Decisions already lock POST_BODY
- blind: idempotent POST on plan row without FLAG → GET 404 — verdict `medium` — verified: `create_living_plan` returns `existing` without checking/healing `plan_complete`
- blind: persist failure raised as `llm_generation_failed` — verdict `low` — rejected (everyday path is UNIQUE race→reload; new error code would need ERRORS list change)
- blind: UNIQUE-race reload untested — verdict `medium` — defer (single-learner desktop; raw UNIQUE tested)
- blind: curriculum not tied to selected path — verdict `false` — LLM returns one curriculum for the propose payload; not per-path
- blind: SCHEDULE `[now, now+7d)` vs `local_dt > now` — verdict `false` — rejected (frozen wording); code correctly uses open left bound
- blind: deferred-work overstates invalid IANA — verdict `false` — deferred entry still covers DST hardening; basic invalid→empty already in-scope
- blind: FK without `PRAGMA foreign_keys=ON` — verdict `low` — defer (store never enabled FK pragma; pre-existing pattern)
- blind: `_loads_paths` silently skips corrupt items — verdict `medium` — verified: corrupt JSON/partial items become empty/truncated `proposed_paths`
- blind: teacherClient missing fetch 404/500 asserts — verdict `low` — patch (small test gap on this story's client surface)
- blind: Always `en`/`ru` vs learner copy — verdict `false` — v1 learner defaults are `en`/`ru`; fallbacks match
- blind: Code Map says learner.py requires placement — verdict `false` — rejected (would edit Code Map); gates live in `create_living_plan`
- edge: `select_path` empty → IndexError — verdict `false` — `parse_path_options` requires 2–3 before select
- edge: non-`LlmGenerationError` from propose — verdict `medium` — verified: only `LlmGenerationError` caught; other exceptions escape as unshaped 500
- edge: LLM latency crosses WEEK_FILL slot — verdict `maybe-false` — defer unverified medium; would need clock recompute after LLM
- edge: plan row without FLAG (idempotent) — verdict `medium` — carried same as blind idempotent/FLAG finding
- edge: DST gap/fold on slot wall time — verdict `false` — OUT_OF_SCOPE / already in deferred-work DST entry
- edge: empty/whitespace LLM secret — verdict `false` — `FileConfig.get_secret` returns `None` for blank
- edge: createLivingPlan 8s client vs 30s LLM — verdict `medium` — verified: `authorizedFetch` defaults 8000; LLM adapter timeout 30s
- edge: unparseable `scheduled_at` on load — verdict `medium` — verified: `_parse_utc_iso` can raise into unshaped 500
- edge: corrupt `proposed_paths_json` — verdict `medium` — carried with `_loads_paths` silent skip
- vg: SQLite round-trip fields never asserted — verdict `medium` — pre-verified gap; POST returns in-memory; GET/idempotent id-only
- vg: UNIQUE-race reload untested — verdict `medium` — carried; disposition defer
- vg: failure paths never assert no plan rows — verdict `medium` — pre-verified gap; only FLAG asserted

## Design Notes

- Atomic txn: plan + lessons + FLAG. `UNIQUE(learner_id)` makes races idempotent.
- WEEK_FILL tests inject fixture `now` only.
- Desktop UX-DR13 chrome is deferred; gate still never opens calendar on FLAG alone.

## Verification

**Commands:**

- `cd services/teacher && uv run pytest` — WEEK_FILL, atomic/UNIQUE, POST/GET, error matrix
- `cd apps/desktop && npm test && npm run build` — profile/gate types green; stub unchanged

**Manual checks:**

- After placement, `POST /living-plan` with bearer → 200 + FLAG on `GET /learner`; second POST idempotent; bad Config/slots → 422; GET resume works
