---
title: "PRD ↔ Architecture Spine Reconciliation"
created: 2026-09-23
sources:
  - prd: "_bmad-output/planning-artifacts/prds/prd-ai-language-teacher-2026-09-22/prd.md"
  - addendum: "_bmad-output/planning-artifacts/prds/prd-ai-language-teacher-2026-09-22/addendum.md"
  - spine: "_bmad-output/planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md"
---

# PRD ↔ Spine Reconciliation

## Summary

The spine **covers v1 topology, ports, and a capability map** for all FR-1..15 and NFR-1/3 at a coarse level. Gaps cluster in **pedagogical invariants** (lesson phases, micro-lesson shape, error taxonomy, placement rules), **learner-visible transparency** (template/plan change summaries), **NFR-2/NFR-4 acceptance detail**, **addendum timing bands**, and **product-only signals** (success metrics, vision tone). Several gaps are **blockers for domain/schema design** if left only in the PRD.

## Landed well (no action required for spine)

| PRD area | Spine evidence |
| -------- | -------------- |
| Stack (Electron + Vue, Python/LangGraph, SQLite, remote LLM) | Stack + Structural Seed |
| Telegram micro-lessons + reminders (FR-12..14) | AD-2, AD-3, Telegram adapter, capability map |
| Single learner, en/ru v1, horizon multi-lang | AD-10, scope frontmatter |
| Living plan / session / Progress ownership | AD-6, AD-7, ER diagram |
| Voice via single port; local-first + optional cloud | AD-9 |
| NFR-1 PII + secrets not in LLM prompts | AD-4, Logging convention |
| NFR-3 no silent failure / retry signaling | AD-5, API errors convention |
| Non-goals: multi-user, multi-target v1, offline LLM, cert track | Deferred table + scope |
| FR bundle mapping | Capability → Architecture Map |

## Did not land (by category)

### A. Pedagogical domain invariants (FR consequences + addendum)

| ID | PRD / addendum requirement | Spine status | Severity |
| -- | -------------------------- | ------------ | -------- |
| Addendum | **Lesson template timing bands** (study-heavy / oral / transfer phase minute ranges) | Not referenced; AD-8 mentions “phase transitions” only | **Blocker** for lesson SM design |
| FR-2 | Placement **must include spoken + listening**; text-only insufficient to finish onboarding | Mapped to “onboarding/placement” only; no voice-mandatory rule | **Blocker** |
| FR-9 | Listening practice requires **comprehension check**, not playback alone | Not stated | **Blocker** (domain activity invariant) |
| FR-4 | **Transfer** templates may include **shadowing / re-say** of corrected lines | Not stated | Ok-to-defer in spine if captured in domain spec; **blocker** if SM is spine-only authority |
| FR-12 | Each micro-lesson: **≥1 L1→Target, ≥1 Target→L1, ≥1 spelling** on new words | MicroLesson entity named; **composition rule missing** | **Blocker** |
| FR-7 | Error stats categorized: **orthography, grammar, incorrect translation, problem topics** | ProgressEvent generic; **no taxonomy** | **Blocker** for persistence + replan |
| FR-6 | Lesson has **topic, planned activities, vocab set** before/at start of practice | Implied by domain SM; not explicit | Ok-to-defer (domain detail) |
| FR-1 | Goals, interests, emphasis, **30/45/60** duration, weekly schedule → plan + reminders | Schedule/reminders implied (AD-2, Telegram); **preference fields not modeled** | Ok-to-defer at spine; note for schema |

### B. Learner-visible transparency (quiet UX/product constraints)

| ID | Requirement | Spine status | Severity |
| -- | ----------- | ------------ | -------- |
| FR-4 | Template choice recorded as **short decision summary** in plan or lesson history | Not in API/event conventions | **Blocker** for Progress/plan read model |
| FR-5 | Learner sees **plan changed** and **what drove the change** (summary) | Replan in domain; **no transparency contract** | **Blocker** for plan mutation events/API |
| FR-3 | Learner can **view Living plan** before/as lesson one begins | Not stated | Ok-to-defer (UX) |
| FR-10 | **Play control** when TTS presented; TTS failure = NFR-3 | Voice port + NFR-3; **UI affordance not architecture** | Ok-to-defer |
| FR-11 | Feedback at **word/phrase** level; **corrected model** (audio and/or text); intonation **best-effort** | NFR-2 bar only; FR-11 depth not bound | Ok-to-defer detail; NFR-2 bar still **blocker** (below) |
| FR-15 | Dashboards: mastery, **error themes by category**, words learned, translation errors | “SQLite projections”; **no projection dimensions** | Ok-to-defer at spine; follows FR-7 taxonomy |

### C. Non-functional requirements (detail)

| ID | Requirement | Spine status | Severity |
| -- | ----------- | ------------ | -------- |
| NFR-2 | **Acceptance bar**: intelligible TTS at lesson pace; ASR captures **full utterances** without manual re-prompt as default | “Quality bar” + defer engines; **acceptance criteria not copied** | **Blocker** for voice adapter sign-off |
| NFR-3 | After failed teacher turn: **resume OR explicit error** with retry/pause — never indefinite hang | Well covered (AD-5, conventions) | Landed |
| NFR-4 | **Documented settings**: LLM/API, Telegram, schedule/reminders, duration/emphasis, voice options; no hidden required settings | Capability map row only; **no doc/discovery invariant** | **Ok-to-defer** at spine (UX/docs); risk if “Config port” assumed sufficient |
| NFR-1 | Strip/redact PII from **prompts and logged model inputs** | AD-4 + logging row | Landed (assumption on Telegram keys aligned) |

### D. Vision, metrics, and tone (product — typically outside spine)

| Item | PRD text | Spine status | Severity |
| ---- | -------- | ------------ | -------- |
| Non-negotiables | Voice + living plan + **Telegram reminders** or “just another chat” | Capabilities present; **product posture not stated** | Ok-to-defer |
| SM-1..SM-4 | Success metrics (~6 months, placement-scaled); **dashboards ≠ success** | Absent | Ok-to-defer |
| Counter-metric | Streak/XP alone ≠ success | Absent | Ok-to-defer |
| Target user / non-users | Personal desktop; Denys job story | Absent | Ok-to-defer |
| Glossary | Living plan, lesson templates, micro-lesson | Partially in naming conventions | Ok-to-defer |
| FR-13 | **Link/unlink** Telegram from desktop | `TelegramLink` in ER; flows not specified | Ok-to-defer (adapter detail) |
| FR-14 | Reminders **respect schedule from FR-1** | Scheduler + Telegram; rule not explicit | Ok-to-defer (domain scheduler rule) |

### E. PRD “deferred to architecture” vs spine

| PRD deferred item | Spine |
| ----------------- | ----- |
| Telegram bot permissions | Explicitly in Deferred table |
| STT/TTS vendor | Deferred; port fixed |
| Local data model profile/SRS/plans | Partial ER (no SRS; plan/session/progress) |

**Gap:** PRD does not require SRS in v1 explicitly in main FR list; spine ER has no SRS — aligned unless brief requires SRS (out of this reconcile scope).

## Recommended spine follow-ups (priority)

1. **Blocker — domain invariants appendix or AD-12**: micro-lesson composition (FR-12), error categories (FR-7), voice-mandatory placement (FR-2), listening comprehension check (FR-9), addendum **phase timing bands** tied to AD-8 lesson SM.
2. **Blocker — transparency**: plan/template **decision summaries** and **replan rationale** as persisted events or plan revision records (FR-4, FR-5).
3. **Blocker — NFR-2**: paste PRD acceptance bar into AD-9 or Consistency Conventions as validation gate.
4. **Ok-to-defer**: SM-1..SM-4, vision tone, NFR-4 documentation policy, FR-10 UI play controls — track in UX/domain specs unless spine is sole AD record.

## Traceability matrix (FR/NFR → spine)

| Req | In capability map? | In AD/invariants? | Gap |
| --- | ------------------ | ----------------- | --- |
| FR-1..3 | Yes | Partial (AD-10, AD-9) | Placement voice-mandatory; prefs shape |
| FR-4..5 | Yes | AD-6, AD-8 | Decision summary; replan visibility |
| FR-6..9 | Yes | AD-8 | Listening check; phase bands; error taxonomy |
| FR-10..11 | Yes | AD-9 | NFR-2 detail; FR-11 feedback shape |
| FR-12..14 | Yes | AD-2, AD-6 | Micro-lesson composition; schedule respect |
| FR-15 | Yes | AD-6, AD-7 | Dashboard dimensions (follow FR-7) |
| NFR-1 | Yes | AD-4 | — |
| NFR-2 | Referenced | AD-9 | Acceptance criteria |
| NFR-3 | Yes | AD-5 | — |
| NFR-4 | Map only | AD-4 (Config) | Documented-settings policy |
