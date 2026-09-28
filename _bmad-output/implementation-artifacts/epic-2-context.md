# Epic 2 Context: First-run onboarding & Living plan on calendar

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Complete the first-run closed loop: intake and speaking/listening placement seed a revisable Living plan, schedule upcoming lessons, and land the learner on the Outlook-like calendar with a side-panel tip for the first lesson. Post-onboarding Settings for Voice, Schedule («изменить»), and Goals become real saves—not shells. Live «Начать урок» may stay stubbed until Epic 3; success here is a durable plan + calendar climax, not a live lesson.

## Stories

- Story 2.1: Onboarding wizard — greeting, goals, interests, duration, schedule
- Story 2.2: Consent and regulated copy gating
- Story 2.3: Placement — briefing, written, listening, speaking
- Story 2.4: Living plan creation and persistence
- Story 2.5: Living plan full-screen document (view-only)
- Story 2.6: Calendar climax — scheduled events, side-panel tip, stub start CTA
- Story 2.7: Settings wiring — Voice, Schedule edit, Goals

## Requirements & Constraints

- Preferences (goals, interests, emphasis, duration 30/45/60, weekly schedule) persist and drive Living plan, templates, and later reminders; at least one weekly slot is required—zero slots block advance with clear copy.
- Placement must include written, listening (with comprehension check, not playback alone), and real speaking capture; text-only placement cannot complete onboarding; listening/speaking gaps block finish.
- After intake + placement, teacher proposes path option(s), creates a revisable Living plan, and schedules the path into lesson one; learner can view the plan before or as lesson one begins.
- Age under 16 (self-declared at greeting) hard-blocks onboarding with regulated exit—no limited/minor mode in v1; age is not re-asked on consent.
- Explicit consent for mic/voice recording and Telegram; AI disclaimer (not certified teacher / not exam guarantee); Privacy/PII copy; no unqualified certificate or level claims.
- Never send surname, postal/physical address, email, or phone into LLM-bound context; secrets and Telegram identity stay out of prompts.
- Plan-creation and listening/voice failures: explicit error + retry (or exit after bounded failures)—never silent hang or fake “complete” onboarding.
- Settings must document and persist v1 Voice, Schedule/duration, and Goals/emphasis via explicit «Сохранить» (Telegram link may remain stubbed until Epic 4).
- Mid-wizard reopen must resume or restart from last saved step—never silently treat unfinished intake as fully onboarded calendar.

## Technical Decisions

- UI issues commands only; Living plan mutations and scheduled lesson rows go through teacher domain use cases → SQLite. UI cache is projection only.
- Pedagogy/scheduling live in teacher domain behind ports (Voice, LLM, Config); domain does not import Vue, Electron, or vendor SDKs.
- Wire JSON is `snake_case`; errors `{ code, message, retryable }`; loopback HTTP + local Bearer from Epic 1.
- Persist `scheduled_at` as UTC instant **and** learner `timezone`; UI shows learner local time. Domain must not invent times when schedule has no usable slots—error with edit-schedule recovery.
- Persist `target_language` and `L1` on learner/plan (`en` / `ru` for v1).
- Voice capture for speaking placement goes through the Voice port; a stub Voice port is allowed for early integration only if plan difficulty seeding stays blocked until a real capture+score run.
- Before plan creation, readiness-check required Config (LLM/API, and Voice where already required); missing/invalid Config → clear copy + Settings path + retry, not mid-wizard silent failure.
- v1 auto-selects the recommended path (options may be read-only); if selectable options appear later, persist choice before writing plan rows.
- Schedule/duration/timezone changes in Settings must reschedule or cancel orphaned future `scheduled_at` rows (including DST) and refresh calendar projections; cancel/recreate pending reminders for affected lessons.
- Entity IDs: opaque string UUIDs. Learner holds prefs, consent state, timezone, language fields.

## UX & Interaction Patterns

- Working-tool chrome: cool grey surfaces; coral as spark; filled primaries use coral-cta. One wizard screen = one step on bg with surface sections; primary «Далее».
- First-run order: greeting (address + age) → goals/outcome → interests/emphasis → duration → Outlook week-slot schedule → consent → placement briefing → written → listening (play → questions) → speaking dialogue → plan-creation animation «создаём план обучения» → **climax: calendar + side-panel first-lesson tip**. No mandatory Living plan review step; no mandatory «Начать урок» as climax.
- Calendar: timed week default (month available); distinguish at least next (coral-soft emphasis), future scheduled, and today orientation (pill + current-time line; today-tint on today cell only). Side panel beside calendar (not modal): tip on first run; selection shows topic + short plan; Living plan entry loads the document.
- Before Epic 3, «Начать урок» is visibly stubbed/disabled when shown—not broken navigation.
- Living plan: full-screen document (goals / focus / upcoming topics); view-only—no manual section edit; numbered steps / accent rules may appear; show template decision summaries when present (or clear empty). Open from nav/header or side panel.
- Settings: Voice (PTT vs auto-listen, optional mic device); Schedule/duration summary + «изменить» mini-wizard reusing onboarding week-slot UI (not an inline grid on the Settings page); Goals/emphasis. Explicit «Сохранить» only.

## Cross-Story Dependencies

- Strict pipeline: 2.1 intake → 2.2 consent → 2.3 placement → 2.4 plan create → 2.6 calendar climax (marks onboarding complete). 2.5 document can open once a plan exists; not a mandatory wizard step.
- 2.7 Settings wiring builds on Epic 1 Settings shells and 2.1 schedule/prefs; schedule edits must keep calendar projections coherent with 2.4/2.6.
- Depends on Epic 1: runnable desktop + teacher loopback auth, Config/SQLite, design tokens/Russian chrome, empty calendar chrome, Settings shells (esp. LLM/API readiness for 2.4).
- Epic 3 enables live start/resume from calendar gates and consumes Voice prefs from 2.7. Epic 4 owns Telegram link/unlink, reminders from schedule, and Living plan replan (edit path beyond view-only).
