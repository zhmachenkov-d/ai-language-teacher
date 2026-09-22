# PRD Quality Review — AI Language Teacher

## Overall verdict

This PRD is well-suited to hobby/solo stakes: v1 scope, horizon, and non-negotiables (voice, living plan, Telegram cadence) are stated as decisions, not wallpaper. Strategic arc from onboarding through voice and Telegram back to progress is coherent, and success metrics match the real outcome (usable conversation and listening), not vanity activity. What remains at risk is build-time ambiguity on a few FRs without consequences and on NFR-2’s qualitative voice bar—enough to slow story acceptance unless tightened lightly.

## Decision-readiness — strong

Trade-offs are explicit: Vision (§ Vision) separates v1 desktop personal tool from multi-user web horizon; Non-Goals (§ Non-Goals) and addendum (§ Delivery, § Deferred product scope) rule out multi-user, extra languages, offline LLM, and non-Telegram channels. Open Questions (§ Open Questions) correctly defer Telegram permissions and STT/TTS vendor choice to architecture without pretending they are resolved. The certificate track is honestly deferred via `[NOTE FOR PM]` in Non-Goals rather than smuggled into v1.

### Findings

_(None — dimension holds up for stated stakes.)_

## Substance over theater — adequate

Content is earned: a single named learner (§ Target User), a specific L1/target pair, and FR groupings tied to the closed teaching loop. There is no persona sprawl or generic innovation section. NFR-2 (§ NFR-2: Voice quality) leans on the adjective **“very good”**; the paired `[ASSUMPTION]` acknowledges the gap but does not replace a product-specific bar.

### Findings

- **medium** Soft voice quality bar (§ NFR-2: Voice quality) — “Very good” reads like template NFR language until architecture picks vendors; consequences describe learner experience but not a falsifiable check. *Fix:* Add one or two concrete acceptance checks (e.g., intelligible TTS at normal lesson pace; ASR captures full learner utterances in dialogue blocks without manual re-prompt as default).

## Strategic coherence — strong

The thesis is clear: personal desktop teacher with voice-first closed loop, living plan, and Telegram for between-lesson practice and reminders (§ Vision, § Features). FR-4/FR-5/FR-7 chain replanning and template choice to error stats; FR-12–FR-14 tie cadence to Telegram and Progress. Success Metrics (§ Success Metrics) target conversation, listening, and pronunciation—with SM-3 explicitly not claiming a reading breakthrough—and name a counter-metric (streak/XP alone). MVP kind is experience/problem-solving for one operator, not a platform backlog.

### Findings

_(None.)_

## Done-ness clarity — adequate

Most FRs carry testable **Consequences** (e.g., FR-2 text-only placement insufficient; FR-9 comprehension check required; FR-13 link/unlink and sync). Gaps: FR-10 and FR-12 state capability without consequences, so “done” for TTS coverage and micro-lesson flows is underspecified for epic/story breakdown. FR-4’s “explainable … stored rationale or equivalent” is directionally testable but leaves “equivalent” open. NFR-3 (§ NFR-3) is strong (no silent failure, explicit retry/pause).

### Findings

- **medium** FR-10 lacks verifiable outcomes (§ FR-10: Text and vocabulary TTS) — No Consequences block; unclear whether all lesson text/new words must be playable, latency bounds, or failure behavior. *Fix:* Add 2–3 bullets (e.g., new vocab and primary lesson passages offer play control; TTS failure surfaces like NFR-3).
- **medium** FR-12 lacks verifiable outcomes (§ FR-12: Micro-lesson translation and spelling) — No Consequences for item types, completion rules, or how results feed FR-15/FR-7. *Fix:* Specify minimum exercise shapes (L1↔Target + spelling), completion signal, and stat update path (align with FR-13 consequences).
- **low** Template rationale ambiguity (§ FR-4: Adaptive Lesson templates) — “Stored rationale or equivalent” may diverge in implementation. *Fix:* Name acceptable equivalents (e.g., logged decision record visible in debug or plan UI summary).

## Scope honesty — strong

Non-Goals are explicit and match addendum deferrals. Three inline `[ASSUMPTION]` tags flag intonation limits, PII/Telegram handling, and voice vendor bar (§ FR-11, § NFR-1, § NFR-2). Open-items density is low and appropriate for hobby/solo v1 with architecture owning stack and vendors (addendum § Stack).

### Findings

_(None beyond mechanical Assumptions Index — see Mechanical notes.)_

## Downstream usability — adequate

Glossary terms (§ Glossary) are reused consistently in FRs (Learner, Living plan, Lesson template, Micro-lesson). FR-1–FR-15 and SM-1–SM-4 are contiguous and internally cross-referenced (e.g., FR-13 → FR-1 schedule). Header points to `addendum.md` for stack/Telegram. No User Journey section: acceptable for single-operator hobby shape (§ Target User carries protagonist context), but UX extraction will lean on FR group descriptions rather than narrative flows.

### Findings

- **low** No UJ narratives for UX sourcing (§ Features, § Target User) — Acceptable at hobby/solo stakes; if UX workflow runs next, stories may duplicate flow ordering work. *Fix:* Optional: one short UJ per major group (onboarding, lesson, micro-lesson) with Denys as protagonist—or defer and let UX spec derive from FR order.

## Shape fit — strong

The document is not over-templated: one user, capability-oriented FRs, stack isolated in addendum, rigor matched to hobby/solo while keeping substance (voice + plan + Telegram as non-negotiables). It does not pretend to be a multi-stakeholder consumer PRD.

### Findings

_(None.)_

## Mechanical notes

- **Assumptions Index:** Three inline `[ASSUMPTION]` tags in `prd.md` (FR-11, NFR-1, NFR-2); no Assumptions Index section at end of PRD — roundtrip incomplete for automated extractors.
- **Glossary drift:** None observed; terms align across FRs and Success Metrics.
- **ID continuity:** FR-1–FR-15 and SM-1–SM-4 contiguous; no duplicate IDs.
- **Cross-references:** References to `addendum.md` and product brief path resolve to sibling artifacts; internal FR cross-refs (FR-4, FR-5, FR-7, FR-13, FR-15) resolve.
- **UJ protagonists:** N/A — no UJ IDs; Denys named in Target User only.
