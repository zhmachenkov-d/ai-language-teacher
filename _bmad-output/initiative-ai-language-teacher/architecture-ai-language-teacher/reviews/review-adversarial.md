# Adversarial Architecture Review — ARCHITECTURE-SPINE.md

**Artifact:** `_bmad-output/planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md`  
**Stance:** Red team — construct downstream **features/epics** that satisfy every adopted AD **literally** yet still integrate into incompatible systems.  
**Date:** 2026-09-23  
**Reviewer role:** Adversarial (build-substrate gate)

---

## Verdict

**Conditionally shippable as a spine, not yet safe for parallel epic implementation.**

The spine correctly fixes process topology, hexagonal boundaries, and coarse ownership (teacher owns plan/session/progress). What it does **not** yet pin down are **canonical data contracts**, **single mutation owners per aggregate field**, and **cross-surface serialization rules**. Two honest teams can each cite AD-1 through AD-11 and still ship clashing SQLite shapes, dual checkpoint writers, and REST/stream payloads that never reconcile.

**Severity:** Medium-high for a solo builder (merge conflicts in one head); **high** if Telegram, dashboard, and lesson runtime epics are staffed in parallel without a schema/API AD pass first.

---

## Method

For each finding:

1. Name two **one-level-down** units (mapped to PRD FR groupings in the Capability → Architecture Map).
2. Show **AD compliance** (checklist against AD-1..AD-11 and Consistency Conventions).
3. Describe the **integration clash** (shared entity, dual owner, or divergent mutation path).
4. Propose a **hole to close** — new AD or tightened rule on an existing AD.

“Obey to the letter” means: Python domain use cases only, SQLite sole store, LangGraph never touches DB, loopback API + token, no UI plan writes, etc. The adversary exploits **underspecified seams**, not open AD violations.

---

## Incompatible Pairs (Epic vs Epic)

### Pair 1 — Progress / error taxonomy split

| Unit | Scope (PRD) | Implementation story |
| ---- | ----------- | ---------------------- |
| **Epic A — Error statistics & replan inputs** | FR-7, FR-4, FR-5 | Domain use case `RecordLessonError` persists `ProgressEvent` with structured payload `{ error_kind, grammar_topic_id, template_id, occurrence_count_delta }`. Replan reads aggregates via `PlanRepository.getWeakSpots()`. |
| **Epic B — Micro-lesson completion** | FR-12, FR-13 | Domain use case `CompleteMicroLesson` persists `ProgressEvent` with `{ exercise_type, was_correct, user_answer_hash }` and optional `tags: string[]` for “weak spots.” Telegram adapter only sends commands. |

**AD compliance (both):**

- AD-1: All logic in domain use cases; adapters call API commands only.
- AD-6: “One write-path” — each epic uses a **different** domain use case name but both write `ProgressEvent` rows; neither UI nor Telegram writes SQLite.
- AD-7: SQLite only.
- AD-10: Events carry `target_language` / `L1` on parent learner context.

**Clash:** FR-7 and FR-15 assume **comparable error stats** for FR-4/FR-5; Epic B’s free-form tags never normalize to Epic A’s `grammar_topic_id`. Dashboard epic (FR-15) queries one projection; micro-lessons silently populate a parallel vocabulary. Replan ignores micro-lesson “errors” or double-counts them.

**Hole:** No AD defines **canonical `ProgressEvent` schema**, error taxonomy, or **which use cases may emit which event types**.

**Close with:** **AD-12 (proposed) — Progress event catalog:** Closed set of `ProgressEvent.type` values; JSON payload schema per type; single registry module; micro-lesson and lesson completion must map into shared weak-spot keys consumed by replan.

---

### Pair 2 — Dual checkpoint owners on `LessonSession`

| Unit | Scope | Implementation story |
| ---- | ----- | ---------------------- |
| **Epic A — Lesson template state machine** | FR-6..FR-9 | Domain SM persists resume checkpoint at every phase boundary: `LessonSession.state = { phase_id, phase_payload, sm_version }`. LangGraph invoked only inside phase; returns control to SM before persist. |
| **Epic B — In-phase agent depth (dialogue / comprehension)** | FR-8, FR-9 | LangGraph loop needs mid-phase resume: use case `CheckpointInPhaseSession` writes `LessonSession.state = { graph_thread_id, graph_checkpoint_blob, pending_tool_calls }` after each agent turn (still via domain use case per AD-8). |

**AD compliance (both):**

- AD-8: SM owns phase transitions; LangGraph never writes SQLite; both paths call domain use cases only.
- AD-6: Teacher-only session persist; UI holds projection only.
- AD-7: Single `LessonSession` table.

**Clash:** Same column/document field `state` overwritten by **two legitimate mutation paths** with incompatible shapes. Resume after crash: SM thinks phase is `listening`; graph blob says tool loop in flight. No conflict rule for precedence or merge.

**Hole:** AD-8 names responsibilities but not **checkpoint composition** (SM vs graph layers, versioning, single writer per sub-key).

**Close with:** Tighten **AD-8** or add **AD-13 — Session checkpoint layering:** `LessonSession` stores `{ sm: {...}, graph: {...} }` with explicit merge rules; only `AdvancePhase` may clear `graph`; graph checkpoint use case may not change `sm.phase_id`.

---

### Pair 3 — `LivingPlan` schedule semantics (instant vs window)

| Unit | Scope | Implementation story |
| ---- | ----- | ---------------------- |
| **Epic A — Onboarding & living plan creation** | FR-1, FR-3, FR-5 | `LessonRecord.scheduled_at` as UTC ISO instant; UI displays localized; replan shifts instants. |
| **Epic B — Telegram reminders** | FR-14 | Scheduler port fires on `LessonRecord.due_window_start` / `due_window_end` in **learner-local** semantics; domain use case `GetDueReminders` reads those columns. |

**AD compliance (both):**

- AD-6: Plan mutations teacher-only via domain.
- AD-3/AD-2: Scheduler in service; Telegram adapter hits same API.
- Consistency: “UTC ISO-8601 in storage” — Epic B stores windows as ISO but interprets as local wall-clock boundaries.

**Clash:** Epic A never writes window columns; Epic B never updates `scheduled_at`. Reminders fire on empty windows or wrong days; UI calendar shows instants that reminder logic ignores.

**Hole:** ER diagram shows `LessonRecord` but no AD for **scheduling field model** (single instant vs recurrence vs reminder window).

**Close with:** **AD-14 (proposed) — Plan schedule model:** One authoritative schedule representation (e.g. `scheduled_at_utc` + optional `reminder_offset_minutes` + IANA tz on Learner); derived windows computed in one domain function, not per-adapter.

---

### Pair 4 — Two names for one learner-facing identity

| Unit | Scope | Implementation story |
| ---- | ----- | ---------------------- |
| **Epic A — Privacy & settings** | NFR-1, NFR-4 | Config port + prefs table: `display_name`, notification toggles; Settings UI uses `PATCH /config/prefs`. |
| **Epic B — Goal intake & placement** | FR-1, FR-2 | Domain `Learner` aggregate: `preferred_name` for LLM address in lessons; persisted in learner row via `CompleteOnboarding`. |

**AD compliance (both):**

- AD-4: Secrets in Config port; display name is not a secret — Epic A still uses Config for prefs.
- AD-7: SQLite for both (different tables).
- AD-6: UI commands only.

**Clash:** Teacher prompts use `preferred_name`; Telegram reminders use `display_name` from prefs. User edits one surface; other stays stale. NFR-1 logging rules differ if one field is treated as PII and the other not.

**Hole:** No boundary for **Learner profile (domain)** vs **operational prefs (config)**.

**Close with:** **AD-15 (proposed) — Learner vs prefs split:** Single domain field `Learner.addressing_name` (or explicit sync rule); Config holds secrets/toggles only; UI settings for “what to call me” route through domain command, not Config patch.

---

### Pair 5 — REST vs lesson stream event shapes

| Unit | Scope | Implementation story |
| ---- | ----- | ---------------------- |
| **Epic A — Desktop lesson UI sync** | FR-6..FR-9, NFR-3 | Subscribes to SSE; expects camelCase events `phaseChanged`, `teacherTurn`, `audioReady` matching Vue conventions. |
| **Epic B — Domain SM + error signaling** | AD-5, NFR-3 | FastAPI stream emits snake_case `phase_changed`, `error_retry` with payload `{ code, message, retryable }` aligned with Python domain models. |

**AD compliance (both):**

- AD-5: Push stream for phase/audio/turn/error; commands stay REST.
- AD-3: Single local API facade (REST + stream on same service).
- Consistency table: API errors structured `{ code, message, retryable }` — applies to REST only, not explicitly to stream.

**Clash:** UI never parses error/retry events; silent hang violates NFR-3 in practice while backend “complies.” Phase sync breaks on casing/field names.

**Hole:** No **single wire contract** for stream vs REST (naming, envelope, versioning).

**Close with:** Tighten **AD-5** + Consistency: **OpenAPI + AsyncAPI (or single schema package)** shared by API adapter; one JSON naming policy (document: camelCase on wire); stream events use same `code` enum as REST.

---

### Pair 6 — `LessonRecord` vs in-flight `LessonSession` lifecycle

| Unit | Scope | Implementation story |
| ---- | ----- | ---------------------- |
| **Epic A — Scheduled desktop lessons** | FR-6 | Start lesson creates `LessonSession` linked to `LessonRecord`; complete lesson archives session and marks record `completed`. |
| **Epic B — Ad-hoc “practice block” from plan UI** | FR-6 (stretch interpretation) | `StartPracticeSession` creates `LessonSession` with `lesson_record_id = null`, topic from plan slice; completion writes Progress only. |

**AD compliance (both):**

- AD-6: Session persist for resume; teacher-only writes.
- AD-7: SQLite.
- ER: `LessonRecord ||--o| LessonSession` — optional session link read as “0..1” allowing null FK.

**Clash:** Two session types share one table without discriminator. Resume API returns orphan sessions; replan deletes `LessonRecord` while practice session still references topic snapshot; dashboard double-counts “active lessons.”

**Hole:** No AD for **session kinds** and FK rules when record is absent.

**Close with:** **AD-16 (proposed) — Session taxonomy:** `LessonSession.kind ∈ { scheduled, micro, practice }`; mandatory FK rules; at most one `in_progress` scheduled session per learner.

---

### Pair 7 — Replan mutates plan while lesson is live

| Unit | Scope | Implementation story |
| ---- | ----- | ---------------------- |
| **Epic A — Living plan replan** | FR-5 | `ReplanLivingPlan` replaces upcoming `LessonRecord` rows and template assignments while learner is mid-week. |
| **Epic B — Long lesson runtime** | FR-8, FR-9 | Active `LessonSession` embeds `plan_snapshot_id` captured at start; SM uses snapshot for vocabulary list. |

**AD compliance (both):**

- AD-6: Plan mutations via domain only; session in SQLite.
- AD-8: SM owns session checkpoints.

**Clash:** Epic A invalidates snapshot pointer or deletes record Epic B references. Post-lesson Progress attributes errors to template IDs that no longer exist in plan. No rule for replan **during** `in_progress` session.

**Hole:** AD-6 lists owners but not **concurrency / replan barriers**.

**Close with:** Tighten **AD-6:** Replan must not mutate `LessonRecord` rows tied to an `in_progress` session; or session carries immutable plan slice blob written at start.

---

### Pair 8 — Micro-lesson as Progress-only vs shadow session

| Unit | Scope | Implementation story |
| ---- | ----- | ---------------------- |
| **Epic A — Telegram micro-lessons** | FR-12, FR-13 | Stateless command flow: `MicroLesson` entity + `CompleteMicroLesson` → `ProgressEvent` only; no `LessonSession`. |
| **Epic B — NFR-3 continuity for Telegram** | FR-13 | Treat micro-lesson as resumable: create short `LessonSession` with `kind=micro` for multi-step spelling flow; persist between Telegram messages. |

**AD compliance (both):**

- AD-6: One progress write-path (both end at ProgressEvent).
- AD-3: Telegram → same API.
- Diagram: `MicroLesson ||--o{ ProgressEvent` — no session link drawn.

**Clash:** Epic B creates session rows Epic A’s analytics ignore; FR-15 “active learning time” counts differ; resume endpoints return micro sessions desktop UI cannot render.

**Hole:** ER + AD-6 under-specify **MicroLesson ↔ LessonSession** relationship.

**Close with:** **AD-17 (proposed) — Micro-lesson runtime:** Either explicitly stateless (checkpoint in `MicroLessonAttempt` table) OR always uses `LessonSession` with kind `micro` — pick one; forbid dual patterns.

---

### Pair 9 — Template rationale storage (plan vs debug)

| Unit | Scope | Implementation story |
| ---- | ----- | ---------------------- |
| **Epic A — Adaptive templates in plan** | FR-4 | `LessonRecord.template_rationale` text column updated when template chosen. |
| **Epic B — Explainability for support** | FR-4 consequence | `TemplateDecisionLog` append-only table written by replan use case with JSON audit trail; plan row stores only `template_id`. |

**AD compliance (both):**

- AD-6: Teacher-only plan mutations.
- AD-7: SQLite.

**Clash:** UI “why this lesson?” reads Epic A column; debug tools read Epic B table; values diverge after replan. FR-4 “stored rationale or equivalent” satisfied locally, not globally.

**Hole:** No convention for **explainability artifacts** vs plan row denormalization.

**Close with:** Consistency + **AD-18 (proposed):** Single source for template rationale (normalized log); plan exposes latest via projection/query, not duplicate text fields.

---

### Pair 10 — Voice audio artifact ownership

| Unit | Scope | Implementation story |
| ---- | ----- | ---------------------- |
| **Epic A — Lesson TTS playback** | FR-10 | Voice port caches audio by `content_hash`; stream emits `audioReady { url: "/api/voice/blobs/{id}" }`. |
| **Epic B — Pronunciation feedback** | FR-11 | Voice port stores learner recording blobs under `/api/voice/recordings/{sessionId}`; same port, different path convention. |

**AD compliance (both):**

- AD-9: Single Voice port; no UI cloud calls.
- AD-5: `audioReady` on stream.

**Clash:** Blob lifecycle (TTL, deletion on session end) differs; Epic A deletes cache on replan content change; Epic B retains recordings for stats — orphaned files or broken playback links. Stream `audioReady` ambiguous for TTS vs feedback clip.

**Hole:** Voice port AD fixes boundary, not **artifact types, URLs, retention**.

**Close with:** Tighten **AD-9:** Typed voice artifacts (`tts`, `learner_recording`); retention policy per type; stream event includes `artifact_kind`.

---

### Pair 11 — Local API “facade” versioning split

| Unit | Scope | Implementation story |
| ---- | ----- | ---------------------- |
| **Epic A — Vue desktop client** | UI capability map | Uses `/v1/lesson/start`, bearer token in header. |
| **Epic B — Telegram adapter** | FR-12..14 | Internal client generated from separate hand-written routes `/telegram/hook` + `/api/lesson/complete` (no `/v1` prefix). |

**AD compliance (both):**

- AD-3: Both hit teacher service local API (not Electron IPC).
- AD-4: Loopback + token on every request.

**Clash:** Two route trees on one FastAPI app — still “one service” but **not one contract**. Token scopes, error shapes, and idempotency keys diverge; “same domain” becomes two DTO layers mapping differently onto use cases.

**Hole:** AD-3 says facade but does not require **one versioned OpenAPI surface** for all adapters.

**Close with:** Tighten **AD-3:** All adapters are clients of **one generated OpenAPI**; webhook routes are thin translators into the same command DTOs.

---

### Pair 12 — LangGraph tool calls vs domain Progress writes

| Unit | Scope | Implementation story |
| ---- | ----- | ---------------------- |
| **Epic A — In-phase correction loop** | FR-7, FR-8 | LangGraph tool `record_error` invokes domain use case `RecordLessonError` (AD-8 compliant). |
| **Epic B — Batch statistics at phase end** | FR-7 | SM phase exit use case `FinalizePhaseStats` writes aggregated Progress from in-memory tallies; graph tool path disabled to reduce LLM cost. |

**AD compliance (both):**

- AD-8: Graph persists only via use cases.
- AD-6: Progress write-path exists in both flows.

**Clash:** Double emission or zero emission depending on feature flag per lesson template. FR-7 “recurring patterns available to FR-4/FR-5” breaks silently when templates use Epic B only.

**Hole:** AD-6 “one write-path” reads as **one code path**, not **one logical pipeline per concern**.

**Close with:** Tighten **AD-6:** For lesson errors, either graph tools **or** phase finalize may emit, not both; template metadata selects strategy; events idempotent on `(session_id, error_fingerprint)`.

---

## Cross-Cutting Gaps (Non-Pair)

| Gap | Why adversaries win | Suggested spine addition |
| --- | -------------------- | ------------------------ |
| **Repository vs use-case boundaries** | AD-1/AD-11 without module-level “who may call `PlanRepository.save`” | Rule: repositories callable only from domain use case layer |
| **Idempotency on Telegram/webhook** | AD-3 silent on duplicate delivery | Command idempotency keys for micro-lesson complete |
| **Projection rebuild** | AD-7 allows UI caches but not rebuild story for FR-15 | Define read models as explicit projections with version |
| **`LessonTemplate` versioning** | FR-4 adaptive templates vs persisted session snapshot | Template ID + version on session start |
| **SSE vs WebSocket deferred** | AD-5 invariant holds but client reconnect state differs | Mandate reconnect cursor field in stream protocol |

---

## AD Compliance Matrix (Spine Strength)

| AD | Literal compliance easy? | Parallel epic risk |
| -- | -------------------------- | ------------------ |
| AD-1 | Yes | Low if repos locked |
| AD-2 | Yes | Low |
| AD-3 | Yes | **Medium** — route/DTO sprawl |
| AD-4 | Yes | Low |
| AD-5 | Yes | **High** — schema/naming |
| AD-6 | Yes | **High** — multiple use cases, one table |
| AD-7 | Yes | **Medium** — projection vs truth |
| AD-8 | Yes | **High** — checkpoint layering |
| AD-9 | Yes | **Medium** — artifact lifecycle |
| AD-10 | Yes | Low |
| AD-11 | Yes | Low |

---

## Recommended Next Actions (Spine Authors)

1. **Schema pass:** Add proposed AD-12, AD-13 (or AD-8 tighten), AD-14, AD-16, AD-17 — minimum set before splitting epics.
2. **Wire contract pass:** Unify REST + stream under one schema; resolve camelCase vs snake_case in Consistency Conventions.
3. **Entity lifecycle diagram:** Extend ER section with `MicroLessonAttempt` or mandatory `LessonSession.kind` — eliminate Pair 6/8 ambiguity.
4. **Replan concurrency:** One paragraph under AD-6 for active session barriers (Pair 7).
5. **OpenAPI as gate:** Add acceptance criterion: Telegram and Vue clients generated from same spec (Pair 11).

---

## Finding Index (Quick Reference)

| # | Epics | Clash type | Close |
| - | ----- | ---------- | ----- |
| 1 | FR-7 replan vs FR-12 micro | Shared `ProgressEvent` shape | AD-12 catalog |
| 2 | FR-6 SM vs FR-8/9 graph | Dual checkpoint writer | AD-13 / AD-8 |
| 3 | FR-3 plan vs FR-14 reminders | Schedule field model | AD-14 |
| 4 | NFR-4 settings vs FR-1 intake | Two learner name owners | AD-15 |
| 5 | Lesson UI vs SM stream | Stream vs REST shape | AD-5 + schema |
| 6 | Scheduled vs practice lesson | Session FK ambiguity | AD-16 |
| 7 | FR-5 replan vs live lesson | Plan/session concurrency | AD-6 tighten |
| 8 | FR-12 micro vs NFR-3 resume | Micro session split | AD-17 |
| 9 | FR-4 rationale | Duplicate explainability stores | AD-18 |
| 10 | FR-10 TTS vs FR-11 recordings | Voice artifact paths | AD-9 tighten |
| 11 | Vue vs Telegram | API facade drift | AD-3 tighten |
| 12 | FR-7 graph tool vs phase stats | Duplicate progress paths | AD-6 tighten |

---

*End of adversarial review.*
