# Editorial Review — PRD: AI Language Teacher

**Document:** `prd.md` (1,342 words) · **Addendum skimmed:** `addendum.md` (stack/Telegram deferrals; no PRD conflicts)  
**Reader:** humans · **Style guide:** Microsoft Writing Style Guide  
**Guidance:** hobby/solo PRD — prefer **CONDENSE** over expansion  
**Structure model:** Strategic/Context (Pyramid)

**Read:** This document exists to help PM, UX, architecture, and epic authors scope v1 of a personal desktop AI English teacher (Russian L1), with voice, living plan, and Telegram micro-lessons/reminders, while keeping multi-user and multi-language on the horizon.

---

| Pass | Original Text | Revised Text | Changes |
| ---- | ------------- | ------------ | ------- |
| structure | §Open Questions — full section (~19 words) | CUT; fold into intro italic or single closing line: “No open product blockers; Telegram permissions and STT/TTS vendor → architecture.” | Empty section adds scan cost; addendum + intro already defer stack/Telegram details (saves ~19 words) |
| structure | §Target User — **Non-users (v1)** bullet list (~25 words) | MERGE into §Non-Goals (v1): drop bullets that duplicate Non-Goals; keep one line in Target User: “Solo desktop learner (Denys); not classrooms or generic OSS users.” | True redundancy with Non-Goals and Vision horizon (saves ~30 words) |
| structure | §Features — group **Description** under Onboarding, Plan and lessons, Voice, Between lessons (~63 words across four H3 intros) | CONDENSE each Description to one clause or remove where H3 title + FRs already state scope (e.g. Voice: delete Description; Progress: add none — already lean) | Premature re-summary before FR database; pyramid body should be FRs (saves ~45 words) |
| structure | §NFR-1–NFR-4 — second **Consequences** bullets (~120 words aggregate) | CONDENSE to one bullet per NFR where the second bullet restates the requirement (NFR-2, NFR-3, NFR-4 especially); keep ASSUMPTION lines | Consequence pairs often echo the requirement sentence; hobby PRD does not need double coverage (saves ~70 words) |
| structure | §Non-Goals — certificate bullet + `[NOTE FOR PM: …]` | CONDENSE to “Certificate / exam track (deferred)” — note lives in addendum §Deferred product scope | Duplicate deferral narrative (saves ~12 words) |
| structure | §Glossary — **Micro-lesson** Telegram clause | PRESERVE | Repeats Telegram channel but anchors term before FR-12–FR-14; worth ~8 words for glossary random-access |
| structure | §Success Metrics — closing sentence on FR-15 | PRESERVE | Prevents metric/dashboard conflation; not redundant with FR-15 |
| prose | FR-13 opening: “v1 sends Micro-lessons…” | “V1 sends micro-lessons…” (sentence-case product phase + lowercase **micro-lesson** per glossary) | Inconsistent sentence-start casing vs “V1 stays” in Vision |
| prose | FR-10, FR-12 — no **Consequences** blocks | Consider: add one consequence each OR strip **Consequences** from all thin FRs and rely on statement-only for FR-10/12-style items? | Inconsistent FR schema impedes scanning and downstream parsing |
| prose | FR-4 / Glossary — “transfer / weak-spot repair” (spaces around slash) | Consider: “transfer/weak-spot repair” or em dash for MS style? | Minor; keep if intentional voice |
| prose | §Vision — “not only a personal desktop tool” vs “personal-first **desktop** teacher” | Consider: “personal desktop tool today → multi-user web later” to tighten antecedent? | Small clarity win in opening pyramid block |

---

## Summary

| Metric | Value |
| ------ | ----- |
| Structure recommendations | 5 actionable (2 PRESERVE) |
| Prose recommendations | 3 (1 optional style) |
| Estimated reduction if all structure cuts accepted | ~176 words (~13% of 1,342) |
| Length target | none stated |
| Comprehension trade-offs | Cutting Open Questions and trimming Non-users requires Non-Goals + intro to carry deferrals (already present). Shortening NFR consequences loses explicit “policy” wording on hidden settings and hang states — keep one strong bullet each. |

## Verdict

**Ready with minor edits** — Pyramid shape is correct (Vision → user → glossary → FR pyramid → non-goals → metrics → NFRs). No scope violations vs addendum. Document is already dense for a hobby PRD; polish is mostly deduplication and FR/NFR template consistency, not reorganization.

---

## Top actionable fixes (for author)

1. **Open Questions** — CUT section; one deferral line in intro or after NFRs.
2. **Target User / Non-Goals** — MERGE overlapping non-user bullets into Non-Goals; slim Target User to primary job + persona.
3. **Features (H3 Descriptions)** — CONDENSE or remove redundant group intros (Voice, Between lessons, Onboarding).
4. **Non-Functional Requirements** — CONDENSE second consequence bullets that restate the requirement.
5. **FR-10 / FR-12 (+ prose)** — Align FR template (minimal consequences or statement-only pattern); fix FR-13 “v1” sentence start.

*2 further minor prose items (slash spacing, Vision antecedent); ask to expand.*
