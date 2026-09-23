# PRD extract — UX Discovery

## Product identity
- **Name:** AI Language Teacher
- **One-line purpose:** Personal-first desktop AI language teacher with a closed teaching loop (voice, living plan with scheduled lessons, Telegram reminders) — English target, Russian explanations in v1; horizon is many languages and multi-user web.
- **Audience (v1):** Denys — needs structured English speaking and listening practice tied to a plan and cadence, without hiring a human tutor; reading/work English is already strong.
- **Non-users (v1):** multi-user classrooms; learners needing a polished multi-language OSS product; people who only want text chat or fully offline LLM.

## Form-factor / platforms
- **v1 surface:** personal desktop teacher (stack stated: Electron + Vue; backend Python, possibly LangGraph).
- **Telegram:** v1 channel for Micro-lessons and lesson reminders (not in-app-only for reminders); Learner can link/unlink Telegram from the desktop app.
- **Horizon (not v1):** multi-user web surface; many languages.
- **Offline:** fully offline LLM is out of v1; LLM is remote/API with local keys OK.
- **Devices / mobile / web app (v1):** (none stated beyond desktop + Telegram).

## User journeys / named scenarios
- **Onboarding** — First-run setup: goals, placement (including speaking and listening), duration, schedule, then a Living plan and path into lesson one.
- **Plan and lessons** — Ongoing teaching: adaptive Lesson templates, topic and vocab selection, explanation, error coaching, replanning from stats.
- **Voice** — TTS for materials; ASR-backed correction of pronunciation and intonation.
- **Between lessons and Telegram** — Micro-lessons for vocab translation and spelling; Telegram delivers micro-lessons and lesson reminders.
- **Progress** — Mastery and error dashboards on the desktop app.
- **Lesson template: study-heavy** — warm-up/review → new material → new words → checks → error review (timing bands in addendum).
- **Lesson template: oral** — warm-up/review → dialogue → listening → error review.
- **Lesson template: transfer / weak-spot repair** — recurring-error warm-up → i+1 listening → new-scenario role-play → shadowing/re-say → capture to review; may include shadowing or re-say of corrected lines after role-play or dialogue.

## Functional needs that imply UI surfaces
- **Goal and preference intake (FR-1):** goals, interests, emphasis, lesson duration (30/45/60), weekly schedule; preferences persist; schedule feeds Telegram reminders.
- **Speaking and listening placement (FR-2):** placement with spoken and listening tasks (text-only alone insufficient to finish onboarding).
- **Living plan creation (FR-3):** teacher proposes path option(s), creates Living plan, can start lesson one; learner can view Living plan before or as lesson one begins; plan marked revisable.
- **Adaptive Lesson templates (FR-4):** select study-heavy, oral, or transfer / weak-spot repair; each lesson associated with one template; short decision summary visible in Living plan or lesson history.
- **Replan Living plan (FR-5):** learner can see that the plan changed and what drove the change (summary level).
- **Lesson plan, topic, and topical vocabulary (FR-6):** per-lesson plan, topic, planned activities, vocab set before or at start of practice blocks; explain material; introduce new words.
- **Error explanation and statistics (FR-7):** explain errors (what was wrong and how to avoid); categorize at least orthography, grammar, incorrect translation, and problem topics; feed plan and Progress.
- **Spoken dialogue and role-play (FR-8):** spoken dialogue and role-play with teacher turn-taking; speech captured for feedback.
- **Listening comprehension practice (FR-9):** listening for understanding with comprehension check (e.g. answer, retell, or choice) — not playback alone.
- **Text and vocabulary TTS (FR-10):** play control for primary lesson passages and new vocabulary when presented.
- **Pronunciation and intonation feedback (FR-11):** names issue at word/phrase level; offers corrected model (audio and/or text).
- **Micro-lesson translation and spelling (FR-12):** L1→Target, Target→L1, and spelling checks on new words (at least one of each per Micro-lesson).
- **Telegram delivery of Micro-lessons (FR-13):** link/unlink Telegram from desktop; completion syncs to Progress / error stats.
- **Telegram reminders for upcoming lessons (FR-14):** respect schedule from FR-1.
- **Mastery and error dashboards (FR-15):** mastered material; error/problem themes; words learned and translation errors; available on desktop without Telegram.
- **Documented settings (NFR-4):** settings surfaces for at least LLM/API access, Telegram linkage, schedule/reminders, lesson duration/emphasis, and voice-related options that exist in v1.
- **Lesson continuity on failure (NFR-3):** explicit error with next step (retry / pause lesson) — never indefinite hang.

## Non-functional / UX constraints
- **Voice modalities (non-negotiable v1):** voice for dialogue, listening comprehension, pronunciation; without voice + living plan + Telegram reminders the product is “just another chat.”
- **Privacy (NFR-1):** must not send PII to the LLM (surname, postal/physical address, email, phone); prompts/logged inputs free of those types; assumption that Telegram linkage and API keys are Learner-configured and not injected into LLM prompts as free-text identity.
- **Voice quality (NFR-2):** TTS and speech understanding “very good”; TTS intelligible at normal lesson pace; in dialogue ASR captures full learner utterances without manual re-prompt as default path.
- **Lesson continuity (NFR-3):** no silent failure; retry then inform learner clearly; resumed flow or explicit error with next step.
- **Documented settings (NFR-4):** main and lesson-related settings described in-product and/or docs; no undocumented hidden settings required for normal use.
- **Languages (v1):** Target language English; L1 (explanations) Russian; additional Target languages beyond English out of v1.
- **Offline:** not fully offline LLM in v1.
- **Notifications:** Telegram reminders for scheduled lessons; other reminder channels out of v1.
- **Accessibility / i18n / dark mode / content density:** (none stated).
- **Success counter-metric:** streak/XP alone does not count as success; Progress dashboards support diagnosis but are not substitute success metrics for SM-1–SM-4.

## Brand / voice / tone cues
- (none stated)

## Explicit out-of-scope / anti-goals
- Multi-user accounts / multi-user web (horizon only)
- Additional Target languages beyond English
- Fully offline LLM
- Polished OSS packaging for arbitrary learners
- Certificate-oriented exam track (deferred — intentional override of product brief; revisit after oral loop works)
- Non-Telegram delivery channels for Micro-lessons or reminders
- v1 has no multi-user
- People who only want text chat (non-users)
- Streak/XP alone as success

## Glossary terms (verbatim)
- **Learner** — single local user of the desktop teacher (v1).
- **Target language** — language being learned (v1: English).
- **L1** — explanation / native language (v1: Russian).
- **Living plan** — long-term curriculum that revises from performance and recurring errors.
- **Lesson template** — one of: study-heavy, oral, transfer / weak-spot repair.
- **Micro-lesson** — short between-lesson practice (vocab translate / spelling), delivered via Telegram in v1.

## Open questions / TBD that affect UX
- **[ASSUMPTION: FR-11]** Intonation scoring is best-effort with available STT; depth may be limited.
- **[ASSUMPTION: NFR-1]** Telegram account linkage and API keys are configured by the Learner and are not injected into LLM prompts as free text identity.
- **[ASSUMPTION: NFR-2]** Vendor/SLA choice deferred to architecture; voice bar validated on the developer’s machine.
- **Deferred to architecture:** Telegram bot permissions; STT/TTS vendor; local data model for profile/SRS/plans.
- **Horizon timing:** multi-language and multi-user web “within about a year” / Vision horizon — not v1.
- **Certificate track:** deferred; revisit when oral loop works.

## Requirement / UJ IDs
### Functional requirements
- **FR-1** — Goal and preference intake (goals, interests, emphasis, 30/45/60 duration, weekly schedule).
- **FR-2** — Speaking and listening placement (not text-only).
- **FR-3** — Living plan creation after intake/placement; path option(s); start lesson one.
- **FR-4** — Adaptive Lesson templates (study-heavy / oral / transfer); visible decision summary.
- **FR-5** — Replan Living plan; learner sees change and drivers (summary).
- **FR-6** — Lesson plan, topic, topical vocabulary, explanation.
- **FR-7** — Error explanation and statistics (orthography, grammar, translation, topics).
- **FR-8** — Spoken dialogue and role-play with turn-taking.
- **FR-9** — Listening comprehension with comprehension check.
- **FR-10** — Text and vocabulary TTS with play control.
- **FR-11** — Pronunciation and intonation feedback with corrected model.
- **FR-12** — Micro-lesson translation (both directions) and spelling.
- **FR-13** — Telegram delivery of Micro-lessons; link/unlink; sync Progress.
- **FR-14** — Telegram reminders for upcoming lessons.
- **FR-15** — Mastery and error dashboards on desktop.

### Non-functional requirements
- **NFR-1** — Privacy: no PII to the LLM.
- **NFR-2** — Voice quality very good for learning and correction.
- **NFR-3** — Lesson continuity on connectivity failure (retry, then clear error).
- **NFR-4** — Documented settings (in-product and/or docs).

### Success metrics
- **SM-1** — Sustained work/everyday conversation (~15–20+ min) with less freezing; transfer to real people.
- **SM-2** — Follow main thread of familiar-topic films, calls, podcasts.
- **SM-3** — Maintain current reading strength (not v1 breakthrough).
- **SM-4** — Pronunciation clear enough for those conversations; native-identical is not the bar.

### User journey IDs
- (none stated — journeys named as feature sections only, no UJ-* IDs)
