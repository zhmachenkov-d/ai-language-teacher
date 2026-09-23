# Reconcile: Product Brief → PRD

**Date:** 2026-09-22  
**Inputs:**

| Document | Path |
| -------- | ---- |
| Product brief | `_bmad-output/planning-artifacts/briefs/brief-ai-language-teacher-2026-09-22/brief.md` |
| Brief addendum | `_bmad-output/planning-artifacts/briefs/brief-ai-language-teacher-2026-09-22/addendum.md` |
| PRD | `_bmad-output/planning-artifacts/prds/prd-ai-language-teacher-2026-09-22/prd.md` |
| PRD addendum | `_bmad-output/planning-artifacts/prds/prd-ai-language-teacher-2026-09-22/addendum.md` |

**Verdict:** Mostly aligned on v1 core loop (onboarding → living plan → adaptive voice lessons → between-lesson practice → replan). One **scope conflict** (certificate track) and one **delivery constraint** (Telegram) introduced in PRD. Several brief qualitative differentiators and curriculum-level details are not carried into FRs.

---

## Alignment (brief must-haves → PRD)

| Brief scope / must-have | PRD coverage | Notes |
| ----------------------- | ------------ | ----- |
| Desktop app (Electron + Vue + Python backend) | Addendum stack pointer; no desktop-shell FR | Expected for architecture, not product FR gap |
| English target; Russian L1/explanation | Glossary + implicit in FRs | OK |
| Configurable onboarding (goals, interests, emphasis, 30/45/60, weekly cadence) | **FR-1** | OK |
| Placement including speaking and listening | **FR-2** | OK |
| Living long-term plan; revises with performance | **FR-3**, **FR-5** | OK |
| Adaptive templates: study-heavy, oral, transfer / weak-spot repair | **FR-4** | OK |
| Voice dialogues + listening; error review into plan | **FR-8**, **FR-9**, **FR-7** | OK |
| Vocab micro-sessions + reminders between lessons | **FR-12**, **FR-13**, **FR-14** | Channel narrowed to Telegram (see overrides) |
| Certificate-oriented planning/practice when selected at intake | **Non-Goal** + deferred note | **Conflict** — brief in-scope, PRD out |
| Pronunciation first-class (best-effort STT/TTS) | **FR-10**, **FR-11** + assumption tag | OK |
| Out: other languages, fully offline LLM, polished OSS, web client | Non-Goals + Vision horizon | OK |
| ~6 month success criteria (conversation, listening, reading hold, pronunciation) | **SM-1–SM-4** | Certificate success criterion dropped with track deferral |
| Remote/API LLM with local keys OK | Brief + both addenda | OK |

---

## Scope conflicts

### 1. Certificate-oriented track (brief **in** v1 when selected → PRD **deferred**)

- **Brief (`brief.md` Scope, Success Criteria #4):** Certificate-oriented planning and practice when selected at intake; measurable progress against exam skill profile (passing not required).
- **PRD:** Listed under Non-Goals with `[NOTE FOR PM: deferred — revisit after oral loop works]`; no FR for intake selection, exam profile, or certificate-aligned plan/practice.
- **Impact:** Brief treats certificate as optional v1 path; PRD removes it entirely from v1. Any epic work on “certificate at intake” has no FR anchor until PRD is updated or brief is revised.

### 2. Reminder and micro-lesson delivery channel

- **Brief:** “Reminders” and “vocab micro-sessions” without naming a channel (desktop-local implied by product shape).
- **PRD / PRD addendum:** Telegram is **the** v1 channel for micro-lessons (**FR-13**) and lesson reminders (**FR-14**); non-Telegram channels are Non-Goals.
- **Impact:** Not a brief contradiction, but a **binding v1 constraint** not stated in the executive brief. Architecture and UX must assume Telegram linkage for accountability loop.

---

## Missing or weak FR coverage (brief must-haves / addendum detail)

| Gap | Brief source | PRD state | Severity |
| --- | ------------ | --------- | -------- |
| Certificate path at intake + exam-aligned plan/practice | Scope; Success #4; addendum “certificate profiles” open topic | Deferred Non-Goal | **High** (explicit scope conflict) |
| Transfer template: **shadowing / re-say corrected lines** | Brief addendum lesson templates | **FR-8** role-play/dialogue only; no shadowing block | Medium (pedagogy slice may be lost in implementation) |
| Transfer template: **short i+1 listening** as named block | Brief addendum | **FR-9** generic listening comprehension | Low (likely subsumed; not template-specific) |
| **Lesson template timing bands** (5–15 min blocks per template) | Brief addendum | Not in FRs or NFRs | Low for PRD; curriculum/UX detail for downstream |
| **“Vocab and related”** micro-sessions | Brief addendum between-lessons | **FR-12** limits to translation + spelling | Low–medium (narrower than brief wording) |

No other brief **in-scope v1** bullets lack a reasonable FR mapping once certificate deferral is accepted.

---

## Qualitative ideas dropped or diluted

These appear in the brief but are not reflected as product requirements, vision copy, or success framing in the PRD:

1. **Product identity:** “Closed teaching loop and **accountability**,” “not another AI chat,” “teacher-like **continuity**” — PRD describes the loop functionally but does not preserve positioning or anti-chat differentiation for UX/copy.
2. **Problem framing:** Avoidance of **SaaS dependency** and “scheduling a human” — local desktop is stack-implied; motivation is not in PRD problem/user sections.
3. **Pedagogy thesis:** “Quality depends on placement, error memory, plan revision — **not a model moat**” — not carried forward; may matter for architecture/prompt strategy narratives.
4. **Secondary audience (OSS later):** Brief emphasizes generalization via configurable intake/placement/emphasis; PRD lists OSS learners as non-users v1 only — trajectory is thinner.
5. **Parked pedagogy** (brief addendum: personal-corpus SRS, richer i+1 engine, interleaved scheduling, pragmatics drills) — appropriately absent from v1 FRs; PRD Open Questions empty vs brief’s open technical topics (STT/TTS depth, data model, certificate profiles) — only partially mirrored in NFR assumptions.

---

## PRD additions not in brief (expansions, not gaps)

| PRD element | Notes |
| ----------- | ----- |
| **Telegram** non-negotiable for micro-lessons + reminders | PRD addendum “user-stated”; strengthens accountability vs brief’s generic “reminders” |
| **FR-15** mastery/error dashboards | Supports diagnosis; brief mentions progress implicitly via plan/errors, not dashboards |
| **NFR-1–NFR-4** (PII to LLM, voice quality bar, lesson connectivity failure, documented settings) | Appropriate hardening; brief silent |
| Vision **~1 year** horizon for multi-language + multi-user web | Brief Vision is similar but less time-bound |
| **Glossary** narrows Micro-lesson to translate/spelling via Telegram | Operationalizes brief “vocab micro-sessions” |

---

## Intentional overrides (PRD wins over brief)

Document explicitly in PRD; reconcile treats these as **accepted** unless brief is revised:

1. **Certificate-oriented track → v1 Non-Goal** (defer until oral loop proven).
2. **Telegram-only** delivery for between-lesson micro-lessons and scheduled-lesson reminders (other channels later).
3. **Micro-lesson scope** specified as L1↔Target translation and spelling (**FR-12**), not open-ended “vocab and related” practice.

---

## Recommendations (for PM / next PRD edit)

1. **Resolve certificate conflict:** Either restore a minimal FR pair (intake flag + plan tagging against a profile stub) or **edit brief Scope** to match deferral — avoid dual sources of truth.
2. **Brief or PRD Vision:** Add one sentence on **accountability / not-a-chat** if UX and epics should preserve differentiation.
3. **Transfer template:** Consider a consequence under **FR-8** or **FR-4** for shadowing/re-say when transfer template is selected, if brief addendum timing is authoritative curriculum.
4. **Open Questions:** Optionally lift brief addendum items (STT/TTS depth, local data model) into PRD Open Questions — certificate profile question moot while deferred.

---

## Compact summary (for parent agent)

- **Input:** Product brief + brief addendum  
- **Gaps:** (1) Certificate at intake in brief, deferred in PRD — scope conflict + missing FRs. (2) Shadowing/re-say in transfer template not in FRs. (3) Qualitative differentiation (accountability, anti-chat, no SaaS) dropped. (4) Micro-sessions narrowed vs “vocab and related.” (5) Lesson timing bands only in brief addendum.  
- **Intentional overrides:** Certificate v1 deferral; Telegram-only micro-lessons/reminders; FR-12 scope.  
- **File:** `_bmad-output/planning-artifacts/prds/prd-ai-language-teacher-2026-09-22/reconcile-brief.md`
