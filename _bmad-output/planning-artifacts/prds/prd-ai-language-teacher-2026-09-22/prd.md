---
title: "PRD: AI Language Teacher"
status: final
created: 2026-09-22
updated: 2026-09-22
---

# PRD: AI Language Teacher

_For PM / downstream UX, architecture, and epics. Builds on product brief `_bmad-output/planning-artifacts/briefs/brief-ai-language-teacher-2026-09-22/`. Stack and Telegram transport live in `addendum.md`._

## Vision

Within about a year the product is a **full AI language teacher**: many languages, and a **multi-user web** surface — not only a personal desktop tool. v1 stays the personal-first **desktop** teacher (English target, Russian explanations, closed teaching loop with voice). **v1 has no multi-user.** Multi-language and multi-user web are horizon only.

**Non-negotiable in any v1 cut:** voice (dialogue, listening comprehension, pronunciation), and a living plan with scheduled lessons plus **Telegram reminders** — without those the product is just another chat.

## Target User

**Jobs (v1):** Denys needs structured English speaking and listening practice tied to a plan and cadence, without hiring a human tutor; reading/work English is already strong.

**Non-users (v1):** multi-user classrooms; learners needing a polished multi-language OSS product; people who only want text chat or fully offline LLM.

## Glossary

- **Learner** — single local user of the desktop teacher (v1).
- **Target language** — language being learned (v1: English).
- **L1** — explanation / native language (v1: Russian).
- **Living plan** — long-term curriculum that revises from performance and recurring errors.
- **Lesson template** — one of: study-heavy, oral, transfer / weak-spot repair.
- **Micro-lesson** — short between-lesson practice (vocab translate / spelling), delivered via Telegram in v1.

## Features

### Onboarding

**Description:** First-run setup: goals, placement (including speaking and listening), duration, schedule, then a Living plan and path into lesson one.

#### FR-1: Goal and preference intake

Learner can state goals, interests, emphasis, lesson duration (30/45/60), and weekly schedule.

**Consequences:**

- Preferences persist and drive Living plan and Lesson templates.
- Schedule is available to Telegram reminder delivery.

#### FR-2: Speaking and listening placement

Learner completes a placement that includes spoken and listening tasks, not text-only.

**Consequences:**

- Placement result is stored and used to seed Living plan difficulty.
- Text-only placement alone is insufficient to finish onboarding.

#### FR-3: Living plan creation

After intake and placement, the teacher proposes path option(s) and creates a Living plan, then can start lesson one.

**Consequences:**

- Learner can view the Living plan before or as lesson one begins.
- Plan is marked revisable (see FR-5).

### Plan and lessons

**Description:** Ongoing teaching: adaptive Lesson templates, topic and vocab selection, explanation, error coaching, replanning from stats.

#### FR-4: Adaptive Lesson templates

Teacher selects study-heavy, oral, or transfer / weak-spot repair from performance and recurring errors.

**Consequences:**

- Each started lesson is associated with exactly one Lesson template.
- Template choice is recorded as a short decision summary visible in the Living plan or lesson history (not only an opaque internal flag).
- Transfer templates may include shadowing or re-say of corrected lines after role-play or dialogue.

#### FR-5: Replan Living plan

Teacher revises the Living plan when learning speed or recurring error patterns warrant change.

**Consequences:**

- Learner can see that the plan changed and what drove the change (summary level).

#### FR-6: Lesson plan, topic, and topical vocabulary

Teacher builds a per-lesson plan, picks topic, explains material, and introduces new words suited to topic and level.

**Consequences:**

- Lesson has a topic, planned activities, and a vocab set before or at start of practice blocks.

#### FR-7: Error explanation and statistics

Teacher explains errors (what was wrong and how to avoid), and records error statistics feeding plan and Progress.

**Consequences:**

- Errors are categorized at least for orthography, grammar, incorrect translation, and problem topics where applicable.
- Recurring patterns are available to FR-4 and FR-5.

#### FR-8: Spoken dialogue and role-play

During lessons, Learner can practice spoken dialogue and role-play in the Target language with teacher turn-taking.

**Consequences:**

- Oral Lesson templates and transfer templates can include dialogue and/or role-play blocks.
- Learner speech is captured for feedback (see Voice features).

#### FR-9: Listening comprehension practice

During lessons, Learner practices listening for understanding (not only TTS playback of study text).

**Consequences:**

- Listening tasks require a comprehension check (e.g. answer, retell, or choice), not playback alone.

### Voice

**Description:** TTS for materials; ASR-backed correction of pronunciation and intonation.

#### FR-10: Text and vocabulary TTS

Teacher can read lesson text and new words aloud in the Target language.

**Consequences:**

- Primary lesson passages and new vocabulary items offer a play control when presented.
- TTS failure follows NFR-3 (retry, then explicit error — no silent skip).

#### FR-11: Pronunciation and intonation feedback

Teacher listens to Learner speech and corrects pronunciation and intonation when wrong.

**Consequences:**

- Feedback names the issue at a usable level (word/phrase) and offers a corrected model (audio and/or text).
- `[ASSUMPTION: intonation scoring is best-effort with available STT; depth may be limited.]`

### Between lessons and Telegram

**Description:** Micro-lessons for vocab translation and spelling; Telegram is the v1 channel for micro-lessons and lesson reminders.

#### FR-12: Micro-lesson translation and spelling

Between lessons, Learner practices new words: L1→Target and Target→L1 translation, plus spelling checks.

**Consequences:**

- Each Micro-lesson includes at least one L1→Target item, one Target→L1 item, and one spelling check on new words.
- Completing a Micro-lesson updates Progress / error stats (same path as FR-13 sync).

#### FR-13: Telegram delivery of Micro-lessons

In v1, Micro-lessons are sent to the Learner’s linked Telegram account.

**Consequences:**

- Learner can link/unlink a Telegram account from the desktop app.
- Micro-lesson completion results sync back into Progress / error stats when completed.

#### FR-14: Telegram reminders for upcoming lessons

In v1, reminders for scheduled lessons are sent via Telegram.

**Consequences:**

- Reminders respect the configured schedule from FR-1.
- Other reminder channels are out of v1.

### Progress

#### FR-15: Mastery and error dashboards

Learner can view progress of mastered material; error/problem themes (orthography, grammar, translation, topics); stats for words learned and translation errors.

**Consequences:**

- Stats update from lessons and Micro-lessons.
- Views are available on the desktop app without requiring Telegram.

## Non-Goals (v1)

- Multi-user accounts / multi-user web
- Additional Target languages beyond English
- Fully offline LLM
- Polished OSS packaging for arbitrary learners
- Certificate-oriented exam track (`[NOTE FOR PM: deferred — revisit after oral loop works]`)
- Non-Telegram delivery channels for Micro-lessons or reminders

## Success Metrics

Horizon **about six months**, scaled by placement level. Counter-metric: streak/XP alone does not count as success.

| ID   | Signal                                                                                                                  |
| ---- | ----------------------------------------------------------------------------------------------------------------------- |
| SM-1 | Hold sustained work/everyday conversation (~15–20+ minutes) with less freezing; increasingly transfer to real people    |
| SM-2 | Follow the main thread of familiar-topic films, calls, and podcasts                                                     |
| SM-3 | Maintain current reading strength (not the v1 breakthrough)                                                             |
| SM-4 | Pronunciation clear enough for those conversations, with deliberate improvement — native-identical is not a success bar |

Progress dashboards (FR-15) support diagnosis; they are not substitute success metrics for SM-1–SM-4.

## Non-Functional Requirements

### NFR-1: Privacy — no PII to the LLM

The system must not send personal identifying information to the LLM, including surname, postal/physical address, email, or phone number.

**Consequences:**

- Prompts and logged model inputs are free of those PII types (strip, redact, or never collect into model-bound context).
- `[ASSUMPTION: Telegram account linkage and API keys are configured by the Learner and are not injected into LLM prompts as free text identity.]`

### NFR-2: Voice quality

Spoken audio (TTS) and speech understanding used for feedback must be **very good** — clear enough for learning and for pronunciation/intonation correction to be useful.

**Consequences:**

- Learner can complete dialogue, listening, and pronunciation loops without audio quality being the blocker.
- Acceptance bar: TTS is intelligible at normal lesson pace; in dialogue blocks ASR captures full learner utterances without requiring a manual re-prompt as the default path.
- `[ASSUMPTION: vendor/SLA choice is deferred to architecture; bar is validated on the developer’s machine.]`

### NFR-3: Lesson continuity on connectivity failure

A lesson must not fail silently. On connectivity/API errors the app retries recovery; if recovery fails, it informs the Learner clearly.

**Consequences:**

- After a failed teacher turn, the Learner either sees a resumed flow or an explicit error with next step (retry / pause lesson) — never an indefinite hang with no message.

### NFR-4: Documented settings

Main application settings and lesson-related settings are described (in-product and/or docs) so the Learner knows what can be configured.

**Consequences:**

- Settings surfaces cover at least: LLM/API access, Telegram linkage, schedule/reminders, lesson duration/emphasis, and voice-related options that exist in v1.
- Undocumented “hidden” settings required for normal use are out of policy for v1.

## Assumptions Index

- FR-11: Intonation scoring is best-effort with available STT; depth may be limited.
- NFR-1: Telegram linkage and API keys are Learner-configured and not injected into LLM prompts as free-text identity.
- NFR-2: STT/TTS vendor choice is architecture-owned; voice bar validated on the developer’s machine.

## Deferred to architecture

Telegram bot permissions; STT/TTS vendor; local data model for profile/SRS/plans.
