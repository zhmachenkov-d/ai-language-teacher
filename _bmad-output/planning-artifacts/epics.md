---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-ai-language-teacher-2026-09-22/prd.md
  - _bmad-output/planning-artifacts/prds/prd-ai-language-teacher-2026-09-22/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/EXPERIENCE.md
  - _bmad-output/specs/spec-ai-language-teacher/SPEC.md
  - _bmad-output/specs/spec-ai-language-teacher/glossary.md
  - _bmad-output/specs/spec-ai-language-teacher/lesson-templates.md
---

# ai-language-teacher: Epic breakdown

## Overview

This document turns the locked PRD, UX, and architecture requirements into an ordered epic and story backlog for implementation. Journey: Epic List → Standing constraints → Requirements inventory → Coverage maps → detailed epics/stories.

## Epic List

### Epic 1: Desktop teacher foundation

**FRs covered:** (none — enables all; NFR4 shell; Architecture starter + AD-1…5, AD-7, AD-15, AD-18; UX-DR1–4, UX-DR6 empty chrome, UX-DR17 Settings shell, UX-DR20 Russian chrome)

### Epic 2: First-run onboarding & Living plan on calendar

**FRs covered:** FR1, FR2, FR3 (+ UX-DR17/10 Settings wiring)

### Epic 3: Live voice lessons

**FRs covered:** FR4, FR6, FR7, FR8, FR9, FR10, FR11

### Epic 4: Telegram cadence, Progress & replan

**FRs covered:** FR5, FR12, FR13, FR14, FR15

## Standing constraints

Apply to every story unless a story explicitly extends them. Stories cite IDs rather than restating full prose.

1. **Source of truth (AD-6):** UI and Telegram clients issue commands only; they must not write Living plan or Progress rows, and UI cache is never the source of truth.
2. **PII (NFR1):** Do not send surname, postal/physical address, email, or phone into LLM-bound context; Telegram identity and API keys stay out of prompts.
3. **Wire (AD-15):** JSON is `snake_case` everywhere; errors use `{ code, message, retryable }` on HTTP and SSE.
4. **Background delivery (AD-2):** Closing the Electron window must not stop teacher-service reminder or Micro-lesson delivery.
5. **Hexagonal (AD-1):** Pedagogy/scheduling live in `services/teacher/domain/`; domain depends on ports only.

## Requirements Inventory

Full prose lives in `inputDocuments`. Below: ID + one-line pointer only.

### Functional Requirements

- **FR1** — Goals, interests, emphasis, duration, weekly schedule → Living plan / templates / reminders
- **FR2** — Placement with speaking + listening (not text-only); seeds plan difficulty
- **FR3** — Path option(s), Living plan create, path to first lesson; plan revisable
- **FR4** — Adaptive Lesson template + learner-visible decision summary (Living plan or history)
- **FR5** — Replan Living plan with visible change summary
- **FR6** — Per-lesson topic, activities, vocab
- **FR7** — Error explanation + stats feeding plan/Progress
- **FR8** — Spoken dialogue / role-play
- **FR9** — Listening with comprehension check
- **FR10** — Passage/vocab TTS with NFR3 failure path
- **FR11** — Pronunciation / intonation feedback
- **FR12** — Micro-lesson L1↔Target + spelling
- **FR13** — Telegram Micro-lesson delivery + link/unlink
- **FR14** — Telegram lesson reminders from FR1 schedule
- **FR15** — Desktop Progress dashboards (mastery, errors, words)

### Nonfunctional Requirements

- **NFR1** — Privacy / no PII to LLM
- **NFR2** — Voice quality bar (TTS intelligible; ASR captures full utterances)
- **NFR3** — Connectivity continuity (retry / pause; no silent hang)
- **NFR4** — Documented Settings for all v1-required options

### Additional Requirements (architecture)

- **Starter** — electron-vite Vue desktop; Python ≥3.12 teacher; pin at scaffold
- **Layout** — `apps/desktop/`; `services/teacher/{domain,ports,adapters,graphs}`
- **AD-1…AD-18** — Hexagonal, topology, loopback HTTP+SSE, trust/token, state ownership, SQLite, LangGraph split, Voice port, languages, ProgressEvent, time model, MicroLesson≠LessonSession, wire, lifecycle gates, pedagogy invariants, app-data layout — see ARCHITECTURE-SPINE.md
- **Deferred** — Exact STT/TTS engines, cloud vendor, Telegram permission matrix, reminder window constants, installers, SRS detail

### UX Design Requirements

- **UX-DR1–4** — Tokens, typography, shapes, spark vs CTA
- **UX-DR5–6** — Calendar event block, week/month, side panel
- **UX-DR7–12** — CTA, numbered steps, chat, mic, listening card, history bar
- **UX-DR13–14** — Onboarding wizard; Due/Incomplete gates
- **UX-DR15–17** — Living plan, Progress, Settings
- **UX-DR18–19** — Connectivity modal; pause/incomplete/history transition
- **UX-DR20–21** — Russian chrome / regulated copy; Telegram daytime + result card + reminders

## Coverage Maps

### FR → Epic

| FR   | Epic                                               |
| ---- | -------------------------------------------------- |
| FR1  | Epic 2                                             |
| FR2  | Epic 2                                             |
| FR3  | Epic 2                                             |
| FR4  | Epic 3 (+ Living plan surface in Epic 2 Story 2.5) |
| FR5  | Epic 4                                             |
| FR6  | Epic 3                                             |
| FR7  | Epic 3                                             |
| FR8  | Epic 3                                             |
| FR9  | Epic 3                                             |
| FR10 | Epic 3                                             |
| FR11 | Epic 3                                             |
| FR12 | Epic 4                                             |
| FR13 | Epic 4                                             |
| FR14 | Epic 4                                             |
| FR15 | Epic 4                                             |

### UX-DR → primary stories

| UX-DR      | Primary stories  |
| ---------- | ---------------- |
| UX-DR1–4   | 1.4              |
| UX-DR5–6   | 1.5, 2.6, 3.1    |
| UX-DR7     | 1.5–1.6, 3.1–3.2 |
| UX-DR8–12  | 3.2–3.7, 3.10    |
| UX-DR13    | 2.1–2.4, 2.6     |
| UX-DR14    | 3.1              |
| UX-DR15    | 2.5, 4.6         |
| UX-DR16    | 4.5              |
| UX-DR17    | 1.6, 2.7, 4.1    |
| UX-DR18–19 | 3.9–3.10         |
| UX-DR20    | 1.4, 2.2         |
| UX-DR21    | 4.3–4.4          |

NFR and AD coverage is cited in story ACs; Standing constraints cover cross-cutting AD-1/2/6/15 and NFR1.

## Epic 1: Desktop teacher foundation

Learner can launch the Electron desktop app with the Python teacher service running in the background, configure documented Settings shells (LLM/API, Voice, Telegram link placeholder), and see branded calendar-home chrome in a ready/empty state — without stopping reminder delivery when the window closes. The process topology is ready for later epics.

### Story 1.1: Scaffold Electron+Vue desktop and Python teacher package

As a developer installing v1,
I want the desktop app and Python teacher service scaffolded in the planned repo layout,
So that I can run a starting shell and build teaching features on a real substrate.

**Acceptance Criteria:**

**Given** a clean repo checkout
**When** the desktop app is scaffolded with electron-vite / `create-electron` (`vue-ts`) under `apps/desktop/`
**Then** Electron main, preload, and Vue 3 renderer exist with pinned Electron/Vue/Vite versions documented at scaffold
**And** the desktop app starts to a placeholder window without requiring the teacher service yet

**Given** the teacher service scaffold
**When** `services/teacher/` is created with `domain/`, `ports/`, `adapters/` (api, persistence, llm, voice, telegram, config stubs), and `graphs/`
**Then** the package targets Python ≥3.12 with FastAPI and LangGraph family dependencies pinned or declared for pin-at-scaffold
**And** domain modules do not import Vue, Electron, Telegram SDK, or vendor LLM/voice SDKs

**Given** the scaffold is complete
**When** a developer follows the documented install/run commands in project docs (or AGENTS.md running section updated)
**Then** both desktop and teacher packages install cleanly on the developer machine
**And** no secrets (`.env` with real keys) are committed

### Story 1.2: Loopback HTTP API with local auth and Electron service lifecycle

As a Learner,
I want the desktop app to talk to a loopback teacher API with a local auth token, while Electron only manages service lifecycle,
So that teaching logic stays in the service and closing the UI window does not kill background delivery readiness.

**Acceptance Criteria:**

**Given** the teacher service from Story 1.1
**When** the FastAPI adapter binds the local HTTP API
**Then** it listens on loopback only (not LAN interfaces)
**And** every HTTP request without a valid local auth token is rejected

**Given** a running teacher service with a configured local token
**When** the Vue client (or a smoke client) calls a health/status endpoint with the token
**Then** the response succeeds with `snake_case` JSON
**And** errors use `{ code, message, retryable }` shape when applicable

**Given** Electron main as thin host
**When** the desktop app starts
**Then** main starts (or attaches to) the teacher service and can report running/stopped status via lifecycle IPC only
**And** domain commands/queries are not sent over Electron IPC (HTTP only)

**Given** the teacher service is running and the Vue window is open
**When** the Learner closes the window (app may remain in tray/background per host design)
**Then** the teacher service process is not stopped solely because the window closed

**Given** local auth token lifecycle (AD-4)
**When** Electron starts or attaches to the teacher service
**Then** a local token is minted (or loaded) into OS app-data / Config — not hardcoded in the repo
**And** the Vue client obtains the token via lifecycle/preload only (never embeds a committed secret)
**And** clearing app-data or rotating the token invalidates prior tokens; the host can remint on next start

**Given** the teacher service fails to start or attach on app launch
**When** lifecycle status is reported
**Then** UI shows stopped + explicit error with retry — no silent HTTP calls against a dead service

### Story 1.3: Config port, secrets layout, and SQLite app-data store

As a Learner,
I want secrets and durable data stored via the Config port and SQLite under OS app-data,
So that keys stay off LLM prompts and the repo, and the teacher has a single local source of truth.

**Acceptance Criteria:**

**Given** the teacher service from Story 1.2
**When** Config port resolves the learner data directory
**Then** SQLite, secrets, and (later) voice-model cache share one OS app-data layout for both dev and installed builds
**And** secrets are never hardcoded in the repository

**Given** Learner-configured LLM (and placeholder Telegram) secrets entered through Config
**When** those values are persisted
**Then** they are readable only via the Config port with OS file permissions appropriate for a single-user desktop app
**And** they are not injected into LLM-bound context as free-text identity (NFR1)

**Given** no prior learner store
**When** persistence initializes SQLite
**Then** a minimal Learner record can be created/loaded with `target_language`, `L1`, and `timezone` fields (v1 defaults `en` / `ru`)
**And** entity IDs are opaque string UUIDs (see Standing constraints: UI cache is never source of truth)

**Given** an API caller with a valid local token
**When** they read a basic learner/profile or config-status projection
**Then** the response is `snake_case` JSON from SQLite/Config (Standing constraints)

### Story 1.4: Design tokens, dark mode, and Russian app chrome shell

As a Learner,
I want the desktop UI to use the locked design tokens, dark mode, and Russian working-tool chrome,
So that later screens share one visual language instead of ad-hoc styling.

**Acceptance Criteria:**

**Given** the Vue renderer from prior Epic 1 stories
**When** design tokens from DESIGN.md `neutral-cool-lines` are implemented as CSS variables (light + dark pairs: bg, surface, sidebar, ink, muted, line, coral, coral-cta, coral-soft, missed, done, on-coral, today-tint)
**Then** surfaces use cool grey chrome; spark coral is not used as body text fill (UX-DR1, UX-DR4)

**Given** OS theme preference and an in-app manual override
**When** the Learner toggles or the OS theme changes
**Then** the UI switches between light and dark token sets (UX-DR1)

**Given** typography and shape tokens
**When** app chrome renders navigation and panel labels
**Then** stack is `"Segoe UI", "Helvetica Neue", Arial, sans-serif`; nav/body are sentence case; panel/section labels may be ALL CAPS; `{rounded.md}` ~4px for chrome; `{rounded.full}` reserved for future numbered steps/mic (UX-DR2, UX-DR3)

**Given** Russian UI chrome (UX-DR20)
**When** the app shell navigates between Calendar, Living plan, Progress, and Settings
**Then** nav labels are in Russian; routes may be placeholder screens except where later Epic 1 stories fill Calendar/Settings
**And** motion for panel/screen transitions is moderate and respects OS reduce-motion

### Story 1.5: Calendar home empty chrome with side panel

As a Learner,
I want an Outlook-like week/month calendar home with a side panel,
So that I have the primary working surface ready even before lessons are scheduled.

**Acceptance Criteria:**

**Given** the branded app shell from Story 1.4
**When** the Learner opens Calendar home (default post-shell route when not onboarding yet)
**Then** an Outlook-like timed week view is the default grain, with month view available
**And** week/month switcher includes Today / prev / next chrome (UX-DR6)

**Given** today is visible on the calendar
**When** the week or month view renders
**Then** today is oriented with an Outlook-like date pill and current-time line when applicable
**And** `{colors.today-tint}` applies only to the today cell (not a full-app warm wash) (UX-DR5 partial)

**Given** no lesson is selected
**When** the side panel renders beside the calendar (not a modal)
**Then** it shows the empty hint «выберите урок для просмотра краткой информации или истории» (UX-DR6)

**Given** no scheduled lessons exist yet
**When** the calendar grid renders
**Then** it shows an empty timed grid without fake demo events
**And** elevation stays minimal (tonal/line separation, not multi-shadow SaaS)

### Story 1.6: Settings sections shell with explicit save

As a Learner,
I want documented Settings sections with explicit save for LLM/API keys and shells for Voice, Telegram, Schedule, and Goals,
So that I know what can be configured and secrets reach the Config port safely (NFR4).

**Acceptance Criteria:**

**Given** the app shell from Story 1.4
**When** the Learner opens Settings
**Then** full-screen sections exist for: Telegram, Voice, Schedule/duration, Goals/emphasis, LLM/API keys (UX-DR17)
**And** section labels follow working-tool Russian chrome (UX-DR20)

**Given** LLM/API key fields
**When** the Learner enters values and presses «Сохранить»
**Then** values persist via the Config port from Story 1.3
**And** changes are not autosaved on every keystroke

**Given** Telegram, Voice, Schedule/duration, and Goals/emphasis sections
**When** the Learner views them in Epic 1
**Then** each section is visible with clear placeholder or summary chrome
**And** Telegram shows unlinked status and a «Привязать» control that may be non-functional or deep-link stub until Epic 4 (no manual chat-id entry)

**Given** Settings documentation policy (NFR4)
**When** the Learner uses Settings
**Then** in-product labels/descriptions cover at least LLM/API access, Telegram linkage, schedule/reminders, lesson duration/emphasis, and voice options present in v1
**And** no undocumented hidden setting is required for normal Epic 1 use

**Given** the Learner has unsaved field edits in Settings
**When** they navigate away without «Сохранить»
**Then** changes are discarded (or a confirm-save prompt appears) — never silent persist

## Epic 2: First-run onboarding & Living plan on calendar

Learner completes intake and speaking/listening placement, receives a revisable Living plan, and lands on the Outlook-like calendar with scheduled lessons and a first-lesson tip in the side panel. Side-panel «Начать урок» may be stubbed/disabled until Epic 3 wires live start. Settings for Voice, Schedule («изменить»), and Goals are wired for post-onboarding edits.

**Stories:** 2.1 Intake → 2.2 Consent → 2.3 Placement → 2.4 Plan create → 2.5 Plan document → 2.6 Calendar climax → 2.7 Settings wiring

### Story 2.1: Onboarding wizard — greeting, goals, interests, duration, schedule

As a Learner,
I want a step-by-step first-run wizard to set how I’m addressed, goals, interests, lesson duration, and weekly schedule,
So that preferences persist and drive the Living plan and reminders (FR1).

**Acceptance Criteria:**

**Given** the desktop app opens for the first time (no completed onboarding)
**When** the onboarding wizard starts
**Then** each screen is one step on `{colors.bg}` with `{colors.surface}` sections (UX-DR13)
**And** primary actions use coral-cta CTAs («Далее»)

**Given** the greeting step
**When** the Learner enters how to address them and age, then «Далее»
**Then** values persist for later gating/copy
**And** age is collected here only (not repeated on consent)

**Given** goals / interests / emphasis / duration steps
**When** the Learner selects learning goal, desired outcome, interests/emphasis, and duration 30/45/60
**Then** preferences are stored on the Learner via teacher domain/API (Standing constraints)

**Given** the schedule step
**When** the Learner sets weekly slots on an Outlook-like week grid
**Then** schedule persists with learner `timezone` and is available later for reminders (FR1, AD-13)
**And** at least one weekly slot is required before «Далее» — zero slots is blocked with clear copy
**And** the Learner can proceed to the next onboarding story’s steps

**Given** the Learner leaves mid-wizard (unfinished onboarding)
**When** they reopen the app
**Then** behavior is defined (resume wizard or restart from last saved step) and does not silently land on calendar as fully onboarded

### Story 2.2: Consent and regulated copy gating

As a Learner,
I want explicit consent and regulated disclaimers before placement,
So that mic/Telegram use and AI limits are clear and Privacy/PII policy is respected (UX-DR20, NFR1).

**Acceptance Criteria:**

**Given** intake from Story 2.1 is complete
**When** the consent step is shown
**Then** it includes explicit consent for microphone/voice recording and Telegram
**And** it includes an AI disclaimer (not a certified teacher / not an exam guarantee) and Privacy/PII copy aligned with NFR1
**And** age is not re-asked on this step

**Given** minors/age constraints from the greeting age value
**When** the Learner’s self-declared age is under **16** (v1 hard minimum)
**Then** onboarding is hard-blocked: clear regulated copy explains the product is not available; there is an exit path and **no** limited/minor mode in v1
**And** placement and Living plan creation do not run

**Given** the Learner has not accepted required consents
**When** they attempt «Далее»
**Then** they cannot proceed to placement
**And** copy stays plain/explicit (no unqualified certificate or level claims)

**Given** required consents are accepted
**When** the Learner continues
**Then** consent state is persisted via teacher domain/API for later Settings/Telegram flows

### Story 2.3: Placement — briefing, written, listening, speaking

As a Learner,
I want placement that includes written, listening, and speaking tasks,
So that Living plan difficulty is seeded from real skills, not text-only (FR2, AD-17).

**Acceptance Criteria:**

**Given** consents from Story 2.2 are complete
**When** the placement briefing step runs
**Then** it explains what the test is, roughly how long, how scored, and what it affects
**And** the Learner can continue with «Далее»

**Given** the written stage
**When** the Learner answers or the stage timer ends
**Then** the stage result is recorded and the wizard can advance (timer may end the stage)

**Given** the listening stage
**When** the Learner plays audio and answers comprehension questions
**Then** listening is not TTS-of-study-text alone — a comprehension check is required
**And** UI may use Listening card patterns (play → questions) (UX-DR11 partial / UX-DR13)

**Given** listening placement audio fails to load or play
**When** recovery is attempted
**Then** the Learner gets retry, then an explicit error — listening result is withheld until the check completes (no forced skip that counts as pass)

**Given** the speaking stage
**When** the Learner completes a spoken dialogue with the app
**Then** speech is captured via the Voice port (real capture required to store a speaking result that seeds plan difficulty)
**And** a stubbed Voice port may be used in early integration **only** if plan difficulty seeding is explicitly blocked until a real capture+score run (FR2)

**Given** mic denied or Voice capture fails in speaking placement
**When** the Learner cannot complete speaking
**Then** UI offers retry and/or Settings mic path; onboarding cannot complete until a speaking result is stored

**Given** any attempt to finish onboarding after only written (text-only) placement
**When** listening or speaking results are missing
**Then** onboarding cannot be marked complete (FR2)

**Given** all placement stages complete
**When** results are persisted
**Then** placement outcome is available to seed Living plan difficulty in Story 2.4
**And** no surname/address/email/phone is sent in LLM-bound placement prompts (NFR1)

### Story 2.4: Living plan creation and persistence

As a Learner,
I want the teacher to propose path option(s) and create a revisable Living plan after placement,
So that I have a long-term curriculum before lesson one (FR3).

**Acceptance Criteria:**

**Given** LLM/API (and Voice where placement already required it) Config from Story 1.6
**When** Living plan creation is about to start
**Then** a readiness check runs: missing or invalid required Config blocks with clear copy and a path to Settings + retry — not a mid-wizard silent failure

**Given** placement results from Story 2.3 and preferences from Story 2.1
**When** Living plan creation runs
**Then** the teacher domain (LLM-orchestrated where needed) proposes path option(s)
**And** v1 auto-selects the recommended path (options may be shown read-only); if multiple options are shown as selectable later, the chosen option is persisted before plan rows are written
**And** plan difficulty is seeded from placement (only when speaking+listening results are real — see Story 2.3)
**And** UI shows plan-creation animation «создаём план обучения» (UX-DR13)

**Given** a created Living plan
**When** it is persisted
**Then** it is stored via domain use cases / SQLite (AD-6, AD-7) — UI does not write plan rows directly
**And** the plan is marked revisable (FR3 / FR5 later)
**And** `target_language` and `L1` are set (`en` / `ru` for v1) (AD-10)

**Given** schedule preferences from Story 2.1
**When** the plan is created
**Then** upcoming lessons are scheduled with `scheduled_at` UTC + learner `timezone` (AD-13)
**And** at least the path into the first lesson is represented as scheduled lesson record(s)
**And** if schedule has no usable slots, creation errors with edit-schedule recovery — domain does not invent times

**Given** plan creation fails (API/LLM error)
**When** recovery is attempted
**Then** the Learner sees an explicit error with retry — not a silent hang or fake “complete” onboarding (NFR3)
**And** after a bounded number of failures, onboarding pauses with exit/retry — it is never marked complete

### Story 2.5: Living plan full-screen document (view-only)

As a Learner,
I want to open the Living plan as a full-screen document showing goals, focus, and upcoming topics,
So that I can see the plan before or as lesson one begins (FR3, UX-DR15).

**Acceptance Criteria:**

**Given** a persisted Living plan from Story 2.4
**When** the Learner opens Living plan from app nav/header (or calendar side-panel entry)
**Then** a full-screen document shows sections: goals / focus / upcoming topics on `{colors.bg}` with `{colors.surface}` blocks
**And** coral spark/CTA appear only for primary actions/motifs (UX-DR15)

**Given** the Living plan document
**When** the Learner views section content
**Then** there is no manual section edit — changes go through teacher replan later (Epic 4)
**And** numbered plan steps / accent-rule motifs may appear where plan stages are listed (UX-DR8)

**Given** the plan is marked revisable
**When** the document renders
**Then** the Learner can tell the plan is the current teacher-owned curriculum (not a static PDF dump)
**And** data comes from teacher API projections (Standing constraints)

**Given** template decision summaries from completed/started lessons (Epic 3) or empty state
**When** the Living plan document renders
**Then** recent template decision summaries are visible on the plan (or clearly empty) — FR4 is not history-only

**Given** onboarding climax policy (EXPERIENCE Flow 1)
**When** plan creation finishes
**Then** the default climax remains calendar + first-lesson tip (Story 2.6) — Living plan review is available but not a mandatory extra wizard step

### Story 2.6: Calendar climax — scheduled events, side-panel tip, stub start CTA

As a Learner,
I want to land on the calendar after onboarding with my scheduled lessons and a tip for the first lesson,
So that I know how to start without a mandatory Living plan review screen (FR3 calendar climax, UX-DR5/6).

**Acceptance Criteria:**

**Given** Living plan and scheduled lessons from Story 2.4
**When** onboarding completes
**Then** the app opens Calendar home with timed event blocks for scheduled lessons in learner local time (AD-13)
**And** onboarding is marked complete so cold open no longer starts the wizard

**Given** scheduled lesson events on the calendar
**When** they render
**Then** states distinguish at least next (coral-soft emphasis), future scheduled, and today orientation (UX-DR5)
**And** event times match persisted `scheduled_at` + timezone

**Given** the first-run climax
**When** the side panel shows without forcing an immediate start
**Then** it includes short guidance on how to start the first lesson
**And** there is no mandatory «Начать урок» as the climax action (EXPERIENCE Flow 1)

**Given** a next or eligible lesson selected in the side panel
**When** «Начать урок» is shown before Epic 3 is implemented
**Then** the CTA is visibly stubbed or disabled with clear affordance — not a broken navigation
**And** selecting a lesson still shows topic + short plan preview without leaving the calendar

**Given** Living plan entry from the side panel
**When** the Learner opens it
**Then** Story 2.5 document loads for the current plan

### Story 2.7: Settings wiring — Voice, Schedule edit, Goals

As a Learner,
I want Settings to actually save Voice preferences, edit my weekly schedule via a mini-wizard, and update goals/emphasis,
So that post-onboarding configuration matches documented Settings (UX-DR17, UX-DR10, NFR4) instead of remaining a shell.

**Acceptance Criteria:**

**Given** Settings → Voice after onboarding (shell from Story 1.6)
**When** the Learner chooses push-to-talk vs auto-listen-after-teacher-turn and optionally a mic device, then «Сохранить»
**Then** preferences persist via teacher Config/domain (Standing constraints)
**And** lesson mic behavior in Epic 3 can read them (default remains PTT/hold if unset) (UX-DR10)

**Given** Settings → Schedule/duration
**When** the section renders
**Then** it shows a summary of current duration and weekly slots (from Story 2.1)
**And** «изменить» opens a mini-wizard reusing the onboarding Outlook week-slot UI — not an inline full grid on the Settings page (UX-DR17)

**Given** the schedule mini-wizard
**When** the Learner saves changes
**Then** updated schedule and duration persist with learner `timezone` (AD-13)
**And** values remain available to Living plan / reminders (FR1 → FR14)

**Given** existing future scheduled lessons when slots, duration, or timezone change
**When** the mini-wizard saves
**Then** domain reschedules or cancels orphaned `scheduled_at` rows (including DST) and refreshes calendar projections
**And** pending reminders for affected lessons are cancelled/recreated — not left targeting deleted slots

**Given** Settings → Goals/emphasis
**When** the Learner edits goals or emphasis and presses «Сохранить»
**Then** preferences update via teacher domain/API
**And** subsequent Living plan / template inputs can use the new values (no UI-direct plan row writes)

**Given** all Settings saves in this story
**When** values change
**Then** saves are explicit «Сохранить» — not autosave-on-every-keystroke (UX-DR17, NFR4)
**And** wire JSON is `snake_case`; secrets stay out of LLM prompts (NFR1)

**Given** Telegram section
**When** viewed in this story
**Then** link/unlink may still be stubbed until Story 4.1 — this story does not require live Telegram

## Epic 3: Live voice lessons

Learner starts or resumes lessons from calendar (due/incomplete gates), runs study-heavy / oral / transfer templates with dialogue, listening checks, TTS, pronunciation feedback, and error coaching; connectivity failures offer retry or pause — never silent abandon. Stories stay thin vertical slices inside this single epic.

**Stories:** 3.1 Eligibility/gates → 3.2 Session chrome → 3.3 Template+SSE → 3.4 Dialogue → 3.5 Listening → 3.6 TTS → 3.7 Pronunciation → 3.8 Errors/Progress → 3.9 Connectivity/pause → 3.10 Completion/history

### Story 3.1: Lesson eligibility + due/incomplete gates

As a Learner,
I want the teacher to decide when a lesson is next/due/missed/incomplete and to show due/incomplete gates on cold open,
So that I start or resume only when policy allows (AD-16, UX-DR14).

**Acceptance Criteria:**

**Given** scheduled lessons from Epic 2
**When** the domain evaluates eligibility
**Then** each lesson can be classified as at least `next`, `due`, `missed`, or `incomplete`
**And** early start before schedule policy allows is rejected by the service (UI cannot override)

**Given** cold open when both an incomplete session and a due/now lesson exist
**When** gate overlays are evaluated
**Then** Incomplete gate wins first («Продолжить» | go to calendar); Due is deferred until the incomplete session is resolved (AD-16)

**Given** cold open when a lesson is due/now and no incomplete exists
**When** the Due gate overlay appears
**Then** choices are «Начать урок» | «Перейти в календарь»
**And** the gate does not appear merely because a next lesson is scheduled for later
**And** if multiple lessons are simultaneously due/next, domain picks exactly one `lesson_id`; the gate/CTA binds only that lesson

**Given** an incomplete («Не завершен») lesson exists (and Due is not also competing, or Incomplete already won)
**When** the Learner cold-opens the app
**Then** Incomplete gate offers «Продолжить» | go to calendar (UX-DR14)

**Given** calendar side panel for next/missed/incomplete
**When** the Learner selects that event
**Then** «Начать урок» / «Продолжить» are enabled (stub from Story 2.6 removed for eligible states)
**And** a future scheduled lesson (not next, missed, or incomplete) shows preview **without** a start CTA

**Given** missed selected
**When** the event renders
**Then** it uses `{colors.missed}` + exclamation treatment (UX-DR5)
**And** side panel offers recovery: late start (if domain late-start window still open) **or** reschedule / skip-forfeit — missed is not a permanent dead pile with no CTA
**And** recovery updates eligibility/`scheduled_at` via domain (UI does not invent calendar rows)

### Story 3.2: LessonSession start/resume + lesson screen chrome

As a Learner,
I want to start or resume a `LessonSession` into a lesson screen with plan stages, header actions, and mic chrome,
So that I have a durable session to continue later (AD-6, AD-14, UX-DR8/10).

**Acceptance Criteria:**

**Given** an eligible lesson from Story 3.1
**When** the Learner chooses «Начать урок»
**Then** domain creates at most one active `LessonSession` for the learner (AD-14)
**And** if another `LessonSession` is already active, start is rejected (or UI is forced to resume/complete first)
**And** the UI opens the lesson screen (dialogue center, left plan stages, bottom mic bar)

**Given** an incomplete session
**When** the Learner chooses «Продолжить»
**Then** the same `LessonSession` resumes at the unfinished task — not a restart from the beginning (AD-16)
**And** completed tasks remain visible
**And** if a template was already chosen, resume reuses the persisted `template_id` — never re-rolls selection

**Given** the lesson screen chrome
**When** it renders
**Then** left sidebar shows numbered plan steps + accent rules (UX-DR8)
**And** header exposes «Пауза» and «Завершить урок» (secondary chrome OK)
**And** mic control is always visible (round; resting line/muted) even if push-to-talk wiring completes in later stories (UX-DR10)

**Given** the Learner presses «Завершить урок» before all phases are done
**When** early finish is confirmed (confirm dialog required)
**Then** the session is marked incomplete or abandoned per domain rules — **never** auto-completed
**And** Progress writes only for completed tasks; skipped tasks do not get fake success events
**And** early finish is distinct from «Пауза» (pause remains resumable incomplete) and from normal completion (Story 3.10)

**Given** session state
**When** it is persisted
**Then** SQLite/`LessonSession` is source of truth (Standing constraints)
**And** domain owns `phase` (+ resume cursor); any agent scratch stays under `agent_state` without redefining phase (AD-8)

### Story 3.3: Template selection + per-lesson plan/topic/vocab + SSE phases

As a Learner,
I want each started lesson to pick a study-heavy / oral / transfer template, build topic/activities/vocab, and stream phase updates over SSE,
So that the lesson follows pedagogy budgets and the UI stays in sync (FR4, FR6, AD-5, AD-8, AD-17).

**Acceptance Criteria:**

**Given** a new `LessonSession` from Story 3.2
**When** the teacher selects a Lesson template
**Then** exactly one of study-heavy, oral, or transfer/weak-spot is associated with the lesson
**And** a short learner-visible decision summary is persisted (for Living plan / history later)
**And** phase timing bands from `lesson-templates.md` constrain domain phase budgets

**Given** template selection
**When** the per-lesson plan is built
**Then** the lesson has a topic, planned activities, and a vocab set before or at start of practice blocks (FR6)
**And** plan stages appear in the left sidebar numbered steps

**Given** an active lesson
**When** the UI opens the live lesson SSE stream (authenticated local token)
**Then** the service pushes events for phase changes (and is ready for audio-ready / teacher turns / error in later stories)
**And** commands remain HTTP request/response; payloads are `snake_case` (AD-5, AD-15)

**Given** SSE drop or auth failure mid-lesson
**When** the client detects the stream error
**Then** it retries with the current local token; if recovery fails, follow NFR3 / Story 3.9 (`retry` / `pause`) — do not silently end the `LessonSession`

**Given** LangGraph in-phase work
**When** the agent loop runs inside a phase
**Then** it persists only via domain use cases — never SQLite directly (AD-8)
**And** domain SM owns phase transitions

**Given** transfer template selection
**When** the plan includes post-dialogue repair
**Then** the plan may include shadowing or re-say of corrected lines (executed in later dialogue/pronunciation stories)

### Story 3.4: Spoken dialogue and role-play

As a Learner,
I want spoken dialogue and role-play turn-taking in the Target language during oral/transfer phases,
So that I practice real conversation with the teacher (FR8).

**Acceptance Criteria:**

**Given** an oral or transfer lesson phase that includes dialogue/role-play
**When** the teacher starts a dialogue block
**Then** teacher and learner turns appear as chat bubbles (teacher = sidebar fill; learner = coral-soft) (UX-DR9)
**And** content is in the Target language (English); UI chrome stays Russian

**Given** push-to-talk / hold-to-speak (default)
**When** the Learner holds the mic control
**Then** mic shows active coral fill + on-coral icon (UX-DR10)
**And** speech is captured through the Voice port (ASR) for the teacher turn loop

**Given** PTT release yields silence or an empty ASR transcript
**When** the utterance is processed
**Then** UI prompts re-speak; the teacher turn does **not** advance on empty input

**Given** teacher turn-taking
**When** a learner utterance is received
**Then** the teacher responds in-phase via LangGraph + domain ports
**And** SSE/HTTP updates reflect the new teacher turn without polling-only UI

**Given** Settings Voice preference for auto-listen after teacher turn (if enabled)
**When** a teacher turn completes
**Then** the mic may auto-open listen mode per Settings; default remains PTT/hold

**Given** dialogue/role-play in transfer templates
**When** the block completes
**Then** the session can proceed to later repair/shadowing phases without ending the whole lesson

### Story 3.5: Listening comprehension card

As a Learner,
I want listening tasks with a real comprehension check (not playback alone),
So that I practice understanding, not just hearing TTS (FR9, UX-DR11).

**Acceptance Criteria:**

**Given** a lesson phase that includes listening comprehension
**When** the listening step starts
**Then** a Listening card renders (surface + line border + rounded.md) separate from inline teacher chat
**And** the player supports play, pause, scrub/seek, and replay

**Given** A/B/C (or equivalent) comprehension options
**When** the Learner selects an option
**Then** selected state uses coral-soft fill + coral border
**And** submitting an answer counts as a comprehension check (playback alone is insufficient)

**Given** transcript/text for the listening material
**When** the Learner has not yet answered
**Then** transcript/text stays hidden until after the answer

**Given** template/teacher chooses voice answer or retell modality
**When** that modality is selected for the step
**Then** the Learner can respond by voice/retell instead of (or in addition to) choice
**And** a comprehension outcome is still required before the phase advances

**Given** listening material audio
**When** it plays
**Then** audio is delivered via the Voice port (not UI calling cloud voice directly) (AD-9)

### Story 3.6: Passage and vocabulary TTS

As a Learner,
I want play controls for primary lesson passages and new vocabulary in the Target language,
So that I can hear materials clearly during study (FR10, NFR2).

**Acceptance Criteria:**

**Given** primary lesson passages or new vocabulary items are presented
**When** the material card or teacher bubble renders
**Then** a play control is available for TTS in the Target language
**And** audio is produced via the Voice port (local-first; optional cloud only if config-gated) (AD-9)

**Given** the Learner presses play
**When** TTS succeeds
**Then** audio is intelligible at normal lesson pace on the developer machine (NFR2 acceptance bar)
**And** SSE may signal audio-ready for UI sync

**Given** TTS fails (connectivity/API/engine error)
**When** recovery is attempted
**Then** the system retries, then shows an explicit error — never silently skips playback (FR10 / NFR3)

**Given** chat bubbles with teacher text
**When** TTS play is offered
**Then** play sits on teacher bubbles and material cards without putting body text on spark coral (UX-DR4/9)

### Story 3.7: Pronunciation and intonation feedback

As a Learner,
I want feedback when my pronunciation or intonation is wrong, with a corrected model,
So that I can fix spoken errors at word/phrase level (FR11, NFR2, UX-DR9).

**Acceptance Criteria:**

**Given** learner speech captured in dialogue or dedicated pronunciation/shadowing steps
**When** ASR processes the utterance via the Voice port
**Then** full learner utterances are captured in dialogue without requiring a manual re-prompt as the default path (NFR2)
**And** intonation scoring may be best-effort with available STT (FR11 assumption)

**Given** a pronunciation or intonation issue is detected
**When** feedback is shown
**Then** it names the issue at word/phrase level under the learner bubble
**And** it offers a corrected model as audio and/or text (UX-DR9)

**Given** inline pronunciation feedback chrome
**When** it renders
**Then** it uses ink/muted hierarchy with optional coral accent on the corrected fragment — not body text on spark coral fill

**Given** transfer template shadowing / re-say of corrected lines
**When** that phase runs
**Then** the Learner can re-say the corrected line after role-play/dialogue and receive feedback in the same pattern

**Given** feedback generation uses the LLM
**When** prompts are built
**Then** no surname/address/email/phone is included in model-bound context (NFR1)

### Story 3.8: Error coaching + ProgressEvent writes

As a Learner,
I want errors explained and recorded into a shared Progress catalog,
So that patterns feed templates, replan, and Progress dashboards (FR7, AD-12).

**Acceptance Criteria:**

**Given** orthography, grammar, incorrect translation, or problem-topic errors during a lesson
**When** the teacher explains an error
**Then** the explanation covers what was wrong and how to avoid it
**And** the explanation is visible in the lesson UI (Russian is acceptable for explanations)

**Given** an error is recorded
**When** Progress is written
**Then** the write uses the shared `ProgressEvent` schema (same path micro-lessons will use in Epic 4)
**And** category is one of at least `orthography`, `grammar`, `incorrect_translation`, `problem_topic` (optional topic tag allowed)

**Given** recurring error patterns accumulate
**When** template selection or replan inputs are computed later
**Then** those patterns are available from the same Progress store (FR7 → FR4/FR5)

**Given** Progress writes
**When** they occur mid-lesson
**Then** they go through domain use cases only — LangGraph does not write SQLite directly (AD-6, AD-8)

**Given** UI Progress projections
**When** events exist
**Then** desktop can read them via API without requiring Telegram (foundation for FR15 in Epic 4)

### Story 3.9: Connectivity modal + incomplete pause/idle

As a Learner,
I want connectivity failures to offer retry or pause, and mid-lesson pause/close/idle to mark the lesson «Не завершен»,
So that a lesson never silently abandons and I can resume at the unfinished task (NFR3, UX-DR18/19, AD-15/16).

**Acceptance Criteria:**

**Given** a connectivity or API/stream error mid-lesson
**When** recovery fails after retry attempt(s)
**Then** a blocking modal shows plain copy such as «нет связи» with **«Повторить»** | **«Пауза»** (UX-DR18)
**And** the lesson does not auto-abandon or hang indefinitely with no message (NFR3)

**Given** the connectivity modal
**When** the Learner chooses «Повторить»
**Then** the client issues a documented retry command (e.g. `retry` / `retry_turn` per AD-15)
**And** the turn/stream attempt resumes without clearing the `LessonSession`

**Given** the connectivity modal
**When** the Learner chooses «Пауза»
**Then** the session follows the same incomplete path as explicit pause
**And** calendar status becomes «Не завершен» (UX-DR18/19)

**Given** an active lesson
**When** the Learner presses header «Пауза» or closes the window
**Then** progress/history for completed tasks is saved
**And** status is «Не завершен» — resumable at the unfinished task, not a restart (UX-DR19, AD-16)

**Given** prolonged absence during an active lesson (~15 min idle)
**When** the idle threshold elapses
**Then** the system auto-pauses with the same outcome as explicit «Пауза» (UX-DR19)

**Given** the connectivity modal is open
**When** idle time would otherwise reach ~15 min
**Then** the idle timer is suspended while the modal is open; choosing «Пауза» does not also fire a duplicate idle auto-pause

**Given** HTTP/SSE error payloads
**When** errors are returned
**Then** they use `{ code, message, retryable }` and wire JSON remains `snake_case` (AD-15)
**And** there is no offline lesson mode in v1

**Given** resume from incomplete (gate or side-panel «Продолжить» from Story 3.1/3.2)
**When** the session continues
**Then** completed tasks remain visible and work continues at the unfinished task

### Story 3.10: Completion → history mode + template decision summary

As a Learner,
I want a completed lesson to switch into read-only history with outcome and template decision visible,
So that I can review what happened and return to the calendar cleanly (UX-DR12/19; FR4 summary).

**Acceptance Criteria:**

**Given** all planned lesson phases/tasks are finished (including after resume from incomplete)
**When** the teacher completes the lesson (farewell + next scheduled lesson date/time per Flow 2 when a next lesson exists)
**Then** the lesson is marked completed in the domain/calendar projection
**And** if no next scheduled lesson exists, farewell omits the next time (or offers reschedule) but still marks completed
**And** the UI switches into read-only history mode for that lesson without requiring a separate navigation step (UX-DR19)

**Given** history mode
**When** the lesson layout is shown
**Then** header + left plan stages + dialogue tape remain visible in read-only form
**And** live controls «Завершить урок» / «Пауза» and the live Mic control are absent

**Given** history mode
**When** the History bottom bar is shown
**Then** it replaces the mic with lesson outcome / short teacher summary **and** the template decision (study-heavy / oral / transfer) from Story 3.3 (UX-DR12, FR4)
**And** audio replay is available for teacher TTS, learner recordings, and listening materials where captured

**Given** learner recordings retained for history replay
**When** retention policy is applied
**Then** recordings have a defined TTL (or Settings clear) and are deleted on uninstall/app-data wipe; unlink Telegram does not require deleting lesson recordings unless Settings clear is used
**And** mic consent copy (Story 2.2) covers persistent storage for replay — not live capture only

**Given** history mode
**When** the Learner exits
**Then** close/back or «Закончить» returns to calendar home (UX-DR12)

**Given** a completed lesson on the calendar
**When** the Learner selects it and chooses «Открыть историю» from the side panel
**Then** the same read-only history mode opens for that lesson

**Given** history reads
**When** data is fetched
**Then** it comes from teacher API/domain (Standing constraints)
**And** wire JSON remains `snake_case`

## Epic 4: Telegram cadence, Progress & replan

Between lessons, Learner gets Telegram micro-lessons and schedule reminders; on desktop, views Progress dashboards and sees Living plan replans with summary and change history.

**Stories:** 4.1 Telegram link → 4.2 MicroLesson entity → 4.3 Telegram delivery → 4.4 Reminders → 4.5 Progress dashboard → 4.6 Replan

### Story 4.1: Telegram link/unlink via Settings deep-link

As a Learner,
I want to link or unlink my Telegram account from Settings via an external deep-link,
So that Micro-lessons and reminders can reach me without typing a chat-id (FR13, UX-DR17, NFR1).

**Acceptance Criteria:**

**Given** Settings → Telegram section from Story 1.6
**When** Telegram is not linked
**Then** UI shows unlinked status and a primary «Привязать» control (coral-cta) (UX-DR17)
**And** there is no manual chat-id text field

**Given** the Learner presses «Привязать»
**When** link starts
**Then** if Telegram consent was previously declined, the flow re-prompts Telegram consent before opening the deep-link
**And** the app opens an external Telegram / bot deep-link (not an in-app fake form)
**And** link stays **pending** until callback/confirm; on timeout or cancel, Settings remains unlinked (no false linked status)
**And** after a successful callback/confirm path, Settings shows linked status

**Given** Telegram is linked
**When** the Learner unlinks
**Then** link metadata is cleared in teacher domain/SQLite (AD-7)
**And** Settings returns to unlinked status
**And** subsequent Micro-lesson/reminder delivery does not target the old chat until re-linked
**And** in-flight Micro-lesson deliveries/answers are cancelled; stale answer callbacks are rejected

**Given** Telegram bot token / link secrets
**When** they are stored or used
**Then** they go through the Config port (OS app-data permissions) — not committed to the repo
**And** they are never injected into LLM prompts as free-text identity (NFR1, AD-4)

**Given** Telegram adapter code
**When** it is implemented
**Then** the Telegram SDK lives only in adapters — domain imports ports only (AD-1)
**And** Telegram issues domain commands via the same teacher domain as the UI (AD-3) — not a second domain model

**Given** link/unlink API
**When** requests succeed or fail
**Then** wire JSON is `snake_case` and errors use `{ code, message, retryable }` (AD-15)

### Story 4.2: MicroLesson entity + translation/spelling flows

As a Learner,
I want between-lesson Micro-lessons that practice L1↔Target translation and spelling on new words,
So that vocab sticks without opening a full lesson (FR12, AD-14, AD-17).

**Acceptance Criteria:**

**Given** the teacher domain
**When** a Micro-lesson is created
**Then** it is a `MicroLesson` entity distinct from `LessonSession` (AD-14)
**And** completing it does not create or resume a `LessonSession`

**Given** a Micro-lesson for the Learner
**When** its item set is built
**Then** it includes at least one L1→Target translation, one Target→L1 translation, and one spelling check on new words (FR12, AD-17)
**And** items draw from recent/new vocab available to the domain (lesson/plan Progress path)
**And** if vocab is empty, domain skips create (or uses an explicit fallback set) — never persists a Micro-lesson with an empty required item set

**Given** the Learner answers Micro-lesson items
**When** answers are scored
**Then** correct/incorrect outcomes are recorded
**And** errors that update stats use the shared `ProgressEvent` catalog (same schema as Story 3.8) with categories such as `incorrect_translation` / `orthography` as applicable (AD-12)

**Given** Micro-lesson completion
**When** Progress is written
**Then** writes go through domain use cases only — Telegram adapter and LangGraph do not write SQLite directly (AD-6, AD-8)

**Given** a Micro-lesson can be exercised without Telegram UI
**When** a developer or adapter invokes domain create/answer/complete commands (e.g. via local API)
**Then** the full FR12 loop completes and Progress updates
**And** delivery channel wiring remains for Story 4.3 (this story does not require a live Telegram send)

**Given** LLM is used to generate or explain Micro-lesson content
**When** prompts are built
**Then** no surname/address/email/phone or Telegram identity is included in model-bound context (NFR1)

### Story 4.3: Telegram delivery of Micro-lessons + result card

As a Learner,
I want Micro-lessons delivered to my linked Telegram in daytime with a clear result card,
So that I can practice between lessons on my phone (FR13, UX-DR21).

**Acceptance Criteria:**

**Given** Telegram is linked (Story 4.1) and domain readiness rules say a Micro-lesson should be built
**When** create/deliver is evaluated
**Then** cadence defaults to at most one Micro-lesson per local calendar day; prefer rest days over days with a scheduled live lesson (still daytime-only)
**And** if a live `LessonSession` is active, delivery is deferred until the session is inactive
**And** empty-vocab skip follows Story 4.2

**Given** Telegram is linked and a Micro-lesson is ready
**When** the scheduler/teacher delivers
**Then** the Micro-lesson is sent only to the linked Telegram account (FR13)
**And** delivery uses the Telegram adapter — not Electron IPC as a domain bus (AD-2, AD-3)

**Given** Telegram API send fails for a ready Micro-lesson
**When** recovery is attempted
**Then** the item stays undelivered with retryable error + backoff; late retry still respects the daytime window (no night send)

**Given** learner local timezone (AD-13)
**When** Micro-lesson send time is evaluated
**Then** sends occur only in the daytime window ~06:00–21:00 local
**And** no Micro-lesson is sent at night (UX-DR21)

**Given** the Learner completes items in Telegram
**When** answers are submitted
**Then** scoring and Progress writes go through the same domain use cases as Story 4.2
**And** completion results sync into Progress/error stats (FR13)

**Given** Micro-lesson completion in Telegram
**When** the bot shows the result
**Then** a result card shows N correct of M
**And** for each wrong word: meaning + correct translation + error note (translation or spelling) (UX-DR21)

**Given** Progress sync after a Micro-lesson
**When** stats update
**Then** the bot does **not** CTA the Learner to open desktop Progress or Living plan (UX-DR21)

**Given** the desktop window is closed
**When** the teacher service is still running
**Then** Micro-lesson delivery can still occur (AD-2)

**Given** Telegram is unlinked
**When** a Micro-lesson would otherwise send
**Then** it is not delivered to a stale chat; delivery waits until re-linked

### Story 4.4: Telegram lesson reminders (T−15 + at start)

As a Learner,
I want Telegram reminders before and at lesson start time based on my schedule,
So that I don’t miss scheduled sessions (FR14, AD-13, UX-DR21).

**Acceptance Criteria:**

**Given** Telegram is linked and a lesson is scheduled (`scheduled_at` UTC + learner `timezone` from FR1 / AD-13)
**When** local time reaches ~T−15 before the lesson
**Then** Telegram sends a reminder that a lesson starts in 15 minutes and includes the topic when known (UX-DR21)

**Given** the same scheduled lesson
**When** local time reaches the lesson start
**Then** Telegram sends an at-start reminder that it is time to study (topic waiting) (UX-DR21)

**Given** reminder scheduling
**When** times are computed
**Then** they use the UTC instant + learner timezone pair — not a second ad-hoc clock (AD-13)
**And** reminders respect the Learner’s configured weekly schedule from FR1 (FR14)

**Given** v1 reminder policy
**When** delivery channels are considered
**Then** Telegram is the only reminder channel — no email/push/other channels (FR14)

**Given** the desktop window is closed
**When** the teacher service is still running
**Then** reminders can still be sent (AD-2)

**Given** Telegram is unlinked or the lesson is already completed, cancelled, or classified missed per domain rules
**When** a reminder tick fires
**Then** no stale reminder is sent for that lesson

**Given** the device was asleep through a T−15 or at-start window
**When** the teacher service wakes and catches up
**Then** it sends catch-up only if the lesson is still pre-start and not completed/missed; otherwise it skips (no duplicate late spam)

**Given** Settings → Telegram / schedule-reminders documentation
**When** the Learner views Settings
**Then** reminder-related options present in v1 are documented (NFR4) — toggles may be minimal but not hidden undocumented switches

### Story 4.5: Progress dashboard (mastery, errors, words)

As a Learner,
I want a desktop Progress dashboard showing mastery, error themes, and word/translation stats,
So that I can see what to reinforce without opening Telegram (FR15, UX-DR16).

**Acceptance Criteria:**

**Given** the app after onboarding
**When** the Learner opens Progress from app nav/header
**Then** a full-screen single-scroll dashboard opens (not a drawer over calendar) (UX-DR16)

**Given** the Progress dashboard
**When** it renders
**Then** sections appear top→bottom: streak/XP → mastery → error themes → words/translation → Living plan link («что учитель усилит») (UX-DR16)
**And** items can expand inline

**Given** streak/XP chrome (UX-DR16 layout)
**When** values are computed
**Then** streak increments on a calendar day with ≥1 completed lesson **or** completed Micro-lesson in learner timezone; resets after a full local day with neither
**And** XP awards a small fixed amount per completed lesson and per completed Micro-lesson (exact constants documented in code); incomplete/missed award none
**And** «ask teacher» / Living plan CTA remains available even when streak is zero — streak alone is not success

**Given** ProgressEvent data from lessons (Story 3.8) and Micro-lessons (Stories 4.2–4.3)
**When** the dashboard loads
**Then** mastery, error/problem themes (at least orthography, grammar, translation, topics), words learned, and translation-error stats reflect that shared store (FR15, AD-12)

**Given** Telegram is unlinked or unused
**When** the Learner opens Progress
**Then** desktop views still work from lesson-sourced Progress alone (FR15)

**Given** the Living plan link / CTA area
**When** the Learner acts on a gap
**Then** they can ask the teacher to account for the gap **or** open the Living plan — streak alone is not presented as success (UX-DR16 / Flow 5)

**Given** Progress reads
**When** data is fetched
**Then** it comes from teacher API/domain projections (Standing constraints)
**And** wire JSON is `snake_case`

### Story 4.6: Living plan replan + banner + change history

As a Learner,
I want the Living plan to revise when speed or recurring errors warrant it, with a visible summary and change history,
So that I understand what changed and why (FR5, UX-DR15, AD-8/17).

**Acceptance Criteria:**

**Given** recurring error patterns and/or learning-speed signals in Progress (from lessons and Micro-lessons)
**When** domain replan triggers are evaluated
**Then** automatic replan requires measurable evidence (e.g. same error category recurring across ≥2 completed lessons, or Learner-requested replan from Progress/Living plan)
**And** an anti-thrash cooldown applies (at most one automatic replan per 7 local days unless Learner-requested)

**Given** a replan trigger that passes evidence and cooldown checks
**When** replan runs
**Then** the Living plan is revised only via teacher domain use cases (LLM-orchestrated where needed) — UI does not write plan rows directly (AD-6, AD-8)

**Given** a replan completes
**When** a short learner-visible summary is persisted
**Then** it states that the plan changed and what drove the change at summary level (FR5, AD-17)
**And** the Living plan document shows an in-page banner «план обновлён» plus that short summary (UX-DR15)

**Given** the Living plan full-screen document (Story 2.5)
**When** the Learner opens change history
**Then** prior replan summaries are available (UX-DR15)
**And** there is still no manual section edit — Learner requests teacher replan rather than editing sections

**Given** Progress dashboard CTA «ask the teacher» / equivalent from Story 4.5
**When** the Learner requests that the teacher account for a gap
**Then** that request can initiate or queue a teacher replan path through domain commands

**Given** replan uses the LLM
**When** prompts are built
**Then** no surname/address/email/phone or Telegram identity enters model-bound context (NFR1)

**Given** calendar / upcoming topics after replan
**When** the plan’s scheduled path changes
**Then** projections update from domain state (schedule may shift topics/emphasis consistent with the new plan)
**And** schedule mutations for lessons with an active or incomplete `LessonSession` are deferred until that session closes — live session topics do not silently diverge mid-lesson
