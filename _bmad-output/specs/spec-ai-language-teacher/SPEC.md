---
id: SPEC-ai-language-teacher
companions:
  - glossary.md
  - lesson-templates.md
  - ../../planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/DESIGN.md
  - ../../planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/EXPERIENCE.md
  - ../../planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md
sources:
  - ../../planning-artifacts/prds/prd-ai-language-teacher-2026-09-22/prd.md
  - ../../planning-artifacts/prds/prd-ai-language-teacher-2026-09-22/addendum.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# AI Language Teacher (v1)

## Why

**Vision + pain:** Denys needs structured English speaking and listening practice tied to a living plan and cadence without hiring a tutor (reading/work English already strong). v1 is a personal-first **desktop** AI teacher — closed teaching loop with voice, a revisable Living plan, and Telegram micro-lessons/reminders. Without voice and plan+Telegram cadence the product collapses to chat. Multi-language and multi-user web are horizon only (~1 year), not v1.

## Capabilities

- **CAP-1**
  - **intent:** Learner states goals, interests, emphasis, lesson duration (30/45/60), and weekly schedule so preferences drive the Living plan and reminders.
  - **success:** Preferences persist; schedule is available to Telegram reminder delivery; values shape Living plan and Lesson template selection.

- **CAP-2**
  - **intent:** Learner completes placement that includes spoken and listening tasks (not text-only) to seed difficulty.
  - **success:** Placement result is stored and used to seed Living plan difficulty; onboarding cannot finish on text-only placement alone.

- **CAP-3**
  - **intent:** After intake and placement, the teacher proposes path option(s), creates a Living plan, and opens a path into lesson one.
  - **success:** Learner can view the Living plan before or as lesson one begins; plan is marked revisable (CAP-5).

- **CAP-4**
  - **intent:** Teacher selects study-heavy, oral, or transfer/weak-spot Lesson template from performance and recurring errors.
  - **success:** Each started lesson has exactly one template; a short decision summary is visible in the Living plan or lesson history; transfer templates may include shadowing or re-say of corrected lines after role-play/dialogue. Timing bands: `lesson-templates.md`.

- **CAP-5**
  - **intent:** Teacher revises the Living plan when learning speed or recurring error patterns warrant change.
  - **success:** Learner can see that the plan changed and what drove the change at summary level.

- **CAP-6**
  - **intent:** Teacher builds a per-lesson plan: topic, explanation of material, and new words suited to topic and level.
  - **success:** Lesson has a topic, planned activities, and a vocab set before or at start of practice blocks.

- **CAP-7**
  - **intent:** Teacher explains errors (what was wrong and how to avoid) and records error statistics that feed plan and Progress.
  - **success:** Errors categorized at least for orthography, grammar, incorrect translation, and problem topics where applicable; recurring patterns available to CAP-4 and CAP-5.

- **CAP-8**
  - **intent:** During lessons, Learner practices spoken dialogue and role-play in the Target language with teacher turn-taking.
  - **success:** Oral and transfer templates can include dialogue and/or role-play; Learner speech is captured for feedback (CAP-11).

- **CAP-9**
  - **intent:** During lessons, Learner practices listening for understanding, not only TTS playback of study text.
  - **success:** Listening tasks require a comprehension check (answer, retell, or choice) — playback alone is insufficient.

- **CAP-10**
  - **intent:** Teacher reads lesson text and new words aloud in the Target language.
  - **success:** Primary lesson passages and new vocabulary items offer a play control when presented; TTS failure follows continuity constraint (retry, then explicit error — no silent skip).

- **CAP-11**
  - **intent:** Teacher listens to Learner speech and corrects pronunciation and intonation when wrong.
  - **success:** Feedback names the issue at word/phrase level and offers a corrected model (audio and/or text).

- **CAP-12**
  - **intent:** Between lessons, Learner practices new words: L1→Target and Target→L1 translation plus spelling checks.
  - **success:** Each Micro-lesson includes at least one L1→Target item, one Target→L1 item, and one spelling check on new words; completion updates Progress/error stats.

- **CAP-13**
  - **intent:** In v1, Micro-lessons are delivered to the Learner’s linked Telegram account.
  - **success:** Learner can link/unlink Telegram from the desktop app; Micro-lesson completion results sync into Progress/error stats.

- **CAP-14**
  - **intent:** In v1, reminders for scheduled lessons are sent via Telegram.
  - **success:** Reminders respect the schedule from CAP-1; no other reminder channels in v1.

- **CAP-15**
  - **intent:** Learner views mastery of material, error/problem themes, words learned, and translation-error stats.
  - **success:** Stats update from lessons and Micro-lessons; views available on desktop without requiring Telegram.

## Constraints

- v1 is a single-Learner personal desktop product — no multi-user accounts or multi-user web.
- v1 Target language is English only; L1 (explanations) is Russian.
- Any v1 cut must include voice (dialogue, listening, pronunciation) and a Living plan with scheduled lessons plus Telegram reminders.
- Telegram is the only v1 delivery channel for Micro-lessons and lesson reminders.
- Remote/API LLM is in scope; fully offline LLM is not.
- **Privacy:** do not send PII to the LLM — surname, postal/physical address, email, or phone (strip, redact, or never collect into model-bound context).
- **Voice quality:** TTS intelligible at normal lesson pace; in dialogue blocks ASR captures full learner utterances without requiring a manual re-prompt as the default path.
- **Continuity:** on connectivity/API errors retry recovery; if recovery fails, inform clearly with next step (retry / pause lesson) — never indefinite hang with no message.
- **Documented settings:** cover at least LLM/API access, Telegram linkage, schedule/reminders, lesson duration/emphasis, and voice-related options present in v1; undocumented hidden settings required for normal use are out of policy.

## Non-goals

- Multi-user accounts / multi-user web
- Additional Target languages beyond English
- Fully offline LLM
- Polished OSS packaging for arbitrary learners
- Certificate-oriented exam track (deferred until oral loop works)
- Non-Telegram delivery channels for Micro-lessons or reminders

## Success signal

Horizon about six months, scaled by placement level. Streak/XP alone does not count. Demonstrable: (1) hold sustained work/everyday conversation ~15–20+ minutes with less freezing, with increasing transfer to real people; (2) follow the main thread of familiar-topic films, calls, and podcasts; (3) maintain current reading strength; (4) pronunciation clear enough for those conversations with deliberate improvement — native-identical is not the bar. Progress dashboards (CAP-15) support diagnosis; they do not substitute for these signals.

## Assumptions

- CAP-11 intonation scoring is best-effort with available STT; depth may be limited.
- Telegram account linkage and API keys are Learner-configured and are not injected into LLM prompts as free-text identity.
- STT/TTS vendor choice, Telegram bot permissions, and local data model for profile/SRS/plans are architecture-owned (see adopted `ARCHITECTURE-SPINE.md`).
