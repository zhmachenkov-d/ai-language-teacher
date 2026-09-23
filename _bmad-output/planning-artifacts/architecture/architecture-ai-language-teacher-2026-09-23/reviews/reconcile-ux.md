---
title: "UX ↔ Architecture Spine Reconciliation"
created: 2026-09-23
sources:
  - design: "_bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/DESIGN.md"
  - experience: "_bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/EXPERIENCE.md"
  - spine: "_bmad-output/planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md"
---

# UX ↔ Spine Reconciliation

## Summary

The spine **aligns on topology** (thin Electron, local API, event stream, session persist/resume at a headline level, Telegram adapter, Progress write-path). **EXPERIENCE.md** locks many **behavioral contracts** that the spine does not name: calendar-centric scheduling **visibility**, **gate overlays**, **incomplete («Не завершен») lifecycle**, **connectivity modal commands**, **history/read models**, and **scheduler/Telegram timing bands**. Without these in spine or a companion AD, **Vue and teacher-service teams can implement incompatible rules** (e.g. UI shows «Начать урок» while domain rejects; UI restarts lesson while UX promises task-level resume; stream retry without pause→incomplete).

Visual-only content in **DESIGN.md** (tokens, density, coral spark) is correctly out of spine scope.

## Landed well (UX ↔ spine)

| UX constraint | Spine evidence |
| ------------- | -------------- |
| Teacher service owns pedagogy; UI commands only | AD-1, AD-3, AD-6 |
| Window close must not kill reminders/micro-lessons | AD-2 |
| In-progress session durable; UI not source of truth | AD-6, AD-7, ER `LessonSession` |
| Lesson sync via push stream + structured errors (NFR-3 direction) | AD-5, API errors convention |
| Voice/mic/settings secrets via service Config port | AD-4, AD-9, capability map |
| Living plan mutations teacher-only; replan in domain | AD-6, AD-8 |
| Telegram companion + same Progress path | AD-3, AD-6, diagram |
| Offline lesson mode out of v1 | EXPERIENCE + spine Deferred (offline LLM) — aligned |
| PII/consent/disclaimer called out in UX regulated language | AD-4, NFR-1 logging row |

## Quiet UX constraints that did not land

### A. Calendar home & scheduling visibility (IA + read API)

| UX (EXPERIENCE) | Spine status | Divergence risk |
| --------------- | ------------ | --------------- |
| **Calendar home** is default post-onboarding; timed week/month grid; event states: completed, scheduled, **next**, **missed**, **«Не завершен»** | No calendar/read-model; ER has `LessonRecord` only | UI paints states; API may return flat schedule without **next/missed/incomplete** derivation |
| **Side panel CTAs** by state: «Начать урок» (next/missed); **no** start for future-not-next; «Продолжить» for incomplete; «Открыть историю» for completed | No eligibility rules | Service allows early start or hides resume while UI shows CTA |
| **Due gate** only when lesson **due/now**, not merely “next on calendar” | Not stated | Cold-open logic differs between UI heuristic and scheduler |
| **Incomplete gate** on cold open while incomplete exists | Resume mentioned; **gate priority** vs due gate not stated | Both gates possible; order undefined |
| Today orientation (pill, time line) — display only | Ok in UI | Low |

### B. Incomplete / pause / resume (session SM)

| UX (EXPERIENCE) | Spine status | Divergence risk |
| --------------- | ------------ | --------------- |
| «Пауза», window close, **~15 min auto-pause** → **«Не завершен»**; history saved | AD-8 “checkpoints”; no **incomplete status**, no idle timer | Session stays “active” or abandoned; calendar state wrong |
| **Resume at unfinished task**, completed tasks visible — **not** restart from start | AD-6 “persist for resume” only | SM restarts lesson; UX Flow 4 broken |
| Connectivity **«Пауза»** → same incomplete path (no auto-abandon) | AD-5 retry/errors; **pause command → incomplete** not bound | UI pauses; service ends session |
| Lesson completion → **history mode** (read-only layout) | Not in API/event model | UI route without persisted “completed + transcript bundle” contract |

### C. Connectivity modal (NFR-3 UX binding)

| UX (EXPERIENCE) | Spine status | Divergence risk |
| --------------- | ------------ | --------------- |
| Blocking modal: **«Повторить»** \| **«Пауза»**; retry resumes attempt; distinct from offline-out | Stream error/retry yes; **modal-level command pairing** and **no silent drop** not spelled for API | Client invents retry loop; service clears session |
| Mock: `key-connectivity-modal.html` | — | Visual only |

### D. History, template transparency, Living plan

| UX (EXPERIENCE) | Spine status | Divergence risk |
| --------------- | ------------ | --------------- |
| **History bottom bar**: template decision (**study/oral/transfer**) + teacher summary | Same gap as PRD FR-4; spine silent | History UI empty; domain never stores decision summary |
| **Living plan**: replan banner «план обновлён» + **change-history view**; no manual section edit | Replan in AD-8; **revision/summary read API** not stated | UI banner with no backing events |
| Progress: streak/XP → mastery → **error themes** → words → Living plan link | Progress projections generic; **error theme dimensions** follow FR-7 taxonomy (PRD gap) | Dashboard sections empty or wrong shape |

### E. Onboarding, placement, lesson activities (UX behavioral)

| UX (EXPERIENCE) | Spine status | Divergence risk |
| --------------- | ------------ | --------------- |
| Placement: briefing → written → **listening** → **speaking** (voice stages) | Capability map FR-1..3; **voice-mandatory** not in spine (PRD FR-2 gap) | Wizard skips voice; plan invalid |
| **Listening card**: A/B/C check; transcript **hidden until after answer**; player scrub/replay | FR-9 not in spine | Playback-only step in domain |
| Onboarding climax: **calendar + side tip**; no Living plan review; no forced start | UX-only flow | Low if API supports calendar after onboarding |
| Settings: **explicit «Сохранить»**; schedule «изменить» mini-wizard | Config port generic | Autosave API vs UX mismatch (moderate) |

### F. Telegram companion (timing & bind)

| UX (EXPERIENCE) | Spine status | Divergence risk |
| --------------- | ------------ | --------------- |
| Micro-lessons **~06:00–21:00 local** only | Scheduler mentioned; **day window** not stated | Night pushes; UX says never |
| Reminders **T−15** + **at start** with topic | Telegram adapter; **reminder schedule contract** not stated | Wrong reminder times |
| Link via **deep-link / external Telegram** (not manual chat id) | `TelegramLink` in ER; flow not specified | Settings UI vs adapter flow differ |
| Result card: score + per-word error notes; **no separate spelling task type** in v1 UX | `MicroLesson` entity; composition rules absent (PRD FR-12) | Bot task shape vs Progress stats |

### G. DESIGN.md (visual — expected deferral)

| Item | Spine | Note |
| ---- | ----- | ---- |
| neutral-cool-lines, coral spark vs CTA, Outlook dense calendar chrome | N/A | Renderer-only; no service divergence |
| Incomplete event styling (`coral-soft` border + muted label) | N/A | Maps to incomplete **state** in section A |
| Component token names | N/A | Shared naming in UX only |

## Top 5 — blockers vs ok-to-defer

| # | Classification | Gap | Why it blocks UI ↔ service alignment |
| - | -------------- | --- | ------------------------------------ |
| 1 | **Blocker** | **Calendar event state + start/resume eligibility** (next, missed, due/now, incomplete, completed; future-not-next **no start**; due vs incomplete **cold-open gates**) | Spine lacks derived schedule state and rules; calendar + side panel + gates become duplicate schedulers in Vue. |
| 2 | **Blocker** | **«Не завершен» session lifecycle** (explicit pause / window close / **~15 min idle** → incomplete; **task-level resume** with prior tasks visible; anti-restart) | AD-6/AD-8 too coarse; SM and `LessonSession` shape will not match Flow 4 without explicit invariants. |
| 3 | **Blocker** | **NFR-3 lesson failure UX contract**: blocking **retry** vs **pause→incomplete** commands on API/stream; **no auto-abandon** on connectivity/API errors | AD-5 covers events generically; without command semantics, modal actions diverge from domain session state. |
| 4 | **Blocker** | **Persisted read models for history + replan transparency** (template **study/oral/transfer** decision summary on history bar; replan **summary + change history** for Living plan banner) | UX surfaces are specified; spine has no revision/decision fields or query endpoints — empty UI or ad hoc JSON in UI cache (violates AD-7). |
| 5 | **Ok-to-defer** | **Telegram day window (06:00–21:00) + T−15/at-start reminder copy/timing** | Belongs in scheduler/Telegram adapter rules; UX already documents; can live in domain scheduler spec if spine stays thin — **unless** only spine is normative, then promote to **blocker**. |

**Additional ok-to-defer (honorable mention):** DESIGN tokens and Outlook visual density; dark mode; Russian chrome; Progress section **ordering** (once FR-7 taxonomy lands); Settings explicit save batching; onboarding wizard failure edges (Open in EXPERIENCE); full-screen route map (Living plan / Progress / Settings).

## Recommended spine follow-ups

1. **AD or conventions appendix — Schedule & calendar projection**: event states, due vs next vs missed, start/resume eligibility, cold-open gate precedence (incomplete vs due).
2. **Extend AD-6/AD-8 — LessonSession incomplete**: status enum, idle auto-pause policy, checkpoint granularity (activity/task), pause vs complete vs abandon.
3. **Extend AD-5 — NFR-3 command set**: `retry_turn` / `pause_lesson` (names TBD) and stream events that drive connectivity modal; forbid silent session clear on retryable errors.
4. **Transparency records** (align PRD reconcile): template decision on lesson completion; plan revision records for replan banner + history view — SQLite + read API.
5. **Scheduler invariants**: Telegram micro-lesson local time window; reminder offsets — reference UX EXPERIENCE State Patterns table.

## Traceability (UX surfaces → spine)

| UX surface / pattern | Capability map? | Spine detail enough for implementation? |
| -------------------- | --------------- | ---------------------------------------- |
| Calendar home + side panel | Partial (Progress/scheduling implied) | **No** — states & CTAs |
| Due / Incomplete gates | No | **No** |
| Lesson + connectivity modal | NFR-3 row | **Partial** — retry yes; pause→incomplete no |
| Incomplete resume Flow 4 | AD-6, AD-8 | **Partial** |
| Lesson history + bottom bar | AD-6 | **No** — decision summary |
| Living plan + replan banner | AD-6, AD-8 | **No** — change history |
| Onboarding / placement wizard | FR-1..3 row | **Partial** — stage sequence |
| Listening card / mic PTT | Voice + lesson rows | **Partial** — comprehension + settings |
| Progress dashboard | FR-15 row | **Partial** — section dimensions |
| Settings / Telegram link | Config + TelegramLink | **Partial** — bind flow |
| Telegram micro-lessons | FR-12..14 row | **Partial** — time window, reminders |
