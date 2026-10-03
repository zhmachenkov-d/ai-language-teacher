# Architecture Spine Rubric Review — ai-language-teacher

**Artifact:** `_bmad-output/planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md`  
**Reviewer:** Independent rubric walker (good-spine checklist)  
**Date:** 2026-09-23  
**Mechanical lint:** `lint_spine.py` → `ok: true`, 0 findings (structure, AD shape, duplicate IDs)

---

## Overall verdict

**Pass with fixes.** The spine is a strong build substrate for a greenfield personal desktop teacher: hexagonal boundaries, process topology, single API facade, state ownership, SQLite authority, and LangGraph/domain split address the highest-risk pedagogical and dual-writer divergences. Before feature/epic breakdown, tighten a few **wire-protocol and envelope** gaps so independently built UI, API, and persistence slices cannot fork incompatible contracts.

---

## Checklist dimension: Divergence coverage (initiative → features/epics)

**Judgment: adequate — one high gap, several medium tails**

The spine correctly fixes the load-bearing forks for v1: domain vs adapters (AD-1, AD-11), UI-lifetime vs background teaching (AD-2), single local API vs Electron-as-bus (AD-3), trust boundary (AD-4), live lesson sync vs polling (AD-5), plan/progress/session writers (AD-6), durable store (AD-7), lesson controller split (AD-8), voice path (AD-9), language metadata (AD-10). Structural seed and ER sketch give epics a shared vocabulary.

Gaps that still allow incompatible choices one level down:

### Findings

- **high** Local API transport not pinned (AD-3, § Invariants — AD-3) — Rule allows “HTTP **and/or** local IPC.” That is an active fork: Vue renderer can target `http://127.0.0.1` while Electron lifecycle code assumes a different IPC channel, or two adapters implement overlapping surfaces with different shapes. *Prevents* claims “divergent UI vs Telegram contracts” but not “divergent **local** clients.” *Fix:* Adopt one rule, e.g. “All local domain access is HTTP on loopback (FastAPI); Electron must not expose a second domain IPC surface” **or** explicitly defer with a binding invariant: “Exactly one transport; choice recorded in first scaffold AD-amendment before parallel client work.”

- **medium** PRD-deferred data model for profile / SRS / plans not closed (PRD § Deferred to architecture; Capability map; Structural Seed ER) — PRD lists “local data model for profile/SRS/plans” as architecture-owned. Spine models `LivingPlan`, `LessonRecord`, `LessonSession`, `ProgressEvent`, `MicroLesson` but never states whether v1 implements SRS scheduling for micro-lessons or plan-driven vocab only (brief addendum parks “personal-corpus SRS” post-v1). Persistence and Telegram micro-lesson epics could invent separate queue models. *Fix:* Add a one-line **Deferred** row (“SRS algorithm / review queue — out of v1; micro-lessons sourced from LivingPlan vocab”) **or** an AD binding minimum profile fields + explicit non-SRS v1 stance.

- **medium** Scheduler / clock port unspecified (diagram `PSched`, Capability map FR-12..14) — Reminders and micro-lesson cadence are non-negotiable (memlog constraint). AD-2 assigns ownership to the Python service but no AD defines whether scheduling is in-process timer, OS job, or Telegram-driven polling. Scheduler adapter vs domain could diverge on timezone, missed-fire behavior, and duplicate delivery. *Fix:* Short AD or Deferred+invariant: e.g. “Single scheduler adapter in teacher service; domain defines fire rules; UTC storage per conventions.”

- **medium** FR-4 “template decision summary” not bound (PRD FR-4; AD-6, AD-8) — FR-4 requires a visible decision summary for template choice. AD-6 covers plan mutations and progress writes but not where template rationale lives (plan row, `ProgressEvent`, lesson history projection). Lesson-history vs plan UI epics could store rationale in incompatible places. *Fix:* One convention line under Consistency Conventions or narrow AD-6 bullet: “Template choice + summary persisted as domain record referenced by lesson history API.”

- **low** SQLite schema evolution silent (AD-7, Stack) — “Single durable source of truth” without migration ownership invites adapters to hand-edit schema or skip versioning. *Fix:* Defer explicitly (“migration tool chosen at scaffold; all schema changes via teacher-service migrations”) or AD: “Only `adapters/persistence` applies migrations.”

---

## Checklist dimension: AD Rule enforceability

**Judgment: strong — minor soft spots**

Each AD carries Binds / Prevents / Rule. IDs AD-1–AD-11 are unique; lint clean.

| AD | Enforceability note |
| --- | --- |
| AD-1, AD-11 | Enforceable via import lint / package boundaries (mermaid matches Rule). |
| AD-2 | Enforceable via process layout + integration tests (window close, reminder still fires). |
| AD-3 | Enforceable **after** transport fork is removed (see high finding). |
| AD-4 | Loopback bind + bearer token enforceable in FastAPI startup and tests; PII-not-in-prompts needs prompt/log review hooks (Convention: Logging helps, not structural). |
| AD-5 | “Push event stream” enforceable once wire protocol chosen; until then clients cannot implement against one contract. |
| AD-6 | API surface can reject direct plan writes; Telegram “same Progress write-path” enforceable via single domain service entrypoint. |
| AD-7 | Enforceable if UI has no write APIs for durable entities (read-only projections). |
| AD-8 | Enforceable: ban `graphs/` → SQLite imports; require domain use-case calls (code review + lint). |
| AD-9 | Single port interface; cloud path behind config gate — enforceable. |
| AD-10 | Schema + defaults enforceable at persistence boundary. |

### Findings

- **medium** AD-5 vs Deferred SSE/WebSocket (AD-5 Rule; § Deferred) — Rule is enforceable in the abstract (“must push stream”) but not as a **shared contract** until one protocol or a mandatory client abstraction exists. Same class of issue as AD-3 transport. *Fix:* Prefer SSE as default in Rule (aligns with FastAPI `StreamingResponse` + lesson events) and defer WebSocket as alternative only if benchmark fails — **or** elevate “SSE vs WebSocket” from Deferred to decided in AD-5.

- **low** AD-4 PII rule (AD-4, Conventions Logging) — “Must not be injected into LLM prompts” is policy-clear but not mechanically enforceable without redaction tests / static prompt templates. Acceptable at hobby/solo stakes if stories add acceptance tests; note for epic NFR-1.

---

## Checklist dimension: Deferred table — divergence safety

**Judgment: adequate — one item borderline**

| Deferred row | Divergence risk |
| --- | --- |
| STT/TTS engines, cloud voice vendor | Low — AD-9 fixes port; engines are adapter-internal. |
| Exact version pins | Low — lint expects pin-at-scaffold; single scaffold epic. |
| Telegram permission matrix | Low for repo units — bot setup doc; not two code modules picking different Telegram APIs. |
| OS installers | Low — topology fixed by AD-2; packaging is downstream. |
| Certificate track, multi-user web, offline LLM | Out of v1 — no parallel implementation expected. |
| **SSE vs WebSocket** | **Medium–high** — parallel UI stream client and API stream endpoint can ship incompatible protocols while table says “invariant holds either way.” Rubric: if two units could diverge, decide or AD. |

### Findings

- **high** SSE vs WebSocket deferred without anti-fork guard (§ Deferred, AD-5) — See AD-5 finding. *Fix:* Decide in AD-5 or add Deferred caveat: “Implementers must not start stream client/server in separate epics until protocol locked in scaffold.”

---

## Checklist dimension: Named tech — verified current

**Judgment: adequate — intentionally unpinned**

Stack table names Electron, Vue 3, Vite, Python 3, FastAPI, LangGraph, SQLite with explicit **“pin at scaffold”** policy. `lint_spine.py` reports no unpinned-version violation given that policy.

Spot-check (2026): LangGraph 1.x line is active with FastAPI SSE patterns commonly documented; FastAPI + LangGraph + loopback SSE fits AD-5/AD-3 direction. No brownfield version conflict.

### Findings

- **low** Unpinned versions (§ Stack) — By design for first scaffold; risk is drift between desktop and teacher service if pinned at different times. *Fix:* Single scaffold story owns all pins; optional memlog `version` entries at scaffold time.

- **low** Python 3 minor not stated (§ Stack, LangGraph docs) — LangGraph streaming docs emphasize asyncio/context behavior on 3.11+. *Fix:* At scaffold, prefer “Python 3.11+” in stack seed if adopting current LangGraph streaming defaults.

---

## Checklist dimension: Greenfield / brownfield fit

**Judgment: strong**

Memlog records greenfield assumption; spine seeds repo layout and stack without contradicting a non-existent application tree. Paradigm and ADs are prescriptive (appropriate for cold start), not ratification fiction.

### Findings

_(None.)_

---

## Checklist dimension: PRD capability coverage (Capability map)

**Judgment: adequate — one NFR gap**

Map rows align FR groupings to domain locations and AD IDs: onboarding FR-1..3, plan FR-4..5, lessons FR-6..9, voice FR-10..11, Telegram FR-12..14, progress FR-15, NFR-1/NFR-3/NFR-4. PRD non-goals (multi-user, extra languages, offline LLM) reflected in AD-10 and Deferred.

### Findings

- **medium** NFR-2 Voice quality absent from map (§ Capability → Architecture Map; NFR-2 in PRD) — Voice row cites AD-9/AD-1 but does not name NFR-2 acceptance bar (intelligible TTS, full-utterance ASR). Architecture owns vendor/engine choice per PRD assumptions. *Fix:* Add row “Voice quality bar (NFR-2) | Voice port + local eval harness on dev machine | AD-9” or bind NFR-2 to Deferred STT/TTS with explicit validation gate.

- **low** Success metrics SM-1..SM-4 not mapped — Acceptable; SM are product outcomes, not structural forks. No finding required for build substrate.

- **medium** PRD “Deferred to architecture” SRS/plans line — Partially addressed (plans/session/progress); SRS ambiguity remains (see divergence finding).

---

## Checklist dimension: Altitude-owned dimensions (decided / deferred / open)

**Judgment: thin on operational / environmental envelope**

| Dimension | Status in spine |
| --- | --- |
| Design paradigm | Decided — Hexagonal |
| Process / runtime topology | Decided — AD-2 |
| Inter-process/API contract | Partially decided — AD-3 (transport fork) |
| Security / privacy | Decided — AD-4 + conventions |
| Real-time UX sync | Partially decided — AD-5 (protocol fork) |
| Data ownership & persistence | Decided — AD-6, AD-7 |
| Orchestration | Decided — AD-8 |
| Voice | Decided boundary — AD-9; engines deferred |
| i18n horizon | Decided — AD-10 |
| Module graph | Decided — AD-11 |
| Stack families | Decided seed; versions deferred |
| Repo structure | Decided — Structural Seed |
| **Deployment & environments** | **Thin** — “desktop local” implied; no dev/prod/config envelope |
| **Infra / provider** | Implicit — remote LLM, local app; no cloud hosting (OK for v1) |
| **Operations** | **Mostly silent** — backup, updates, health, log retention, service recovery |

### Findings

- **high** Operational / environmental envelope under-specified (initiative altitude; § Stack, § Deferred, AD-2) — AD-2 fixes service vs UI process model but not: SQLite file location/backup, teacher service crash restart, log rotation, update/distribution channel beyond deferred installers, or “dev” vs “installed” config. For a personal desktop app many choices are simple defaults, but **two epics** (Electron packaging vs teacher service) could diverge on data path, port, and token storage. *Fix:* Add short **Deferred** block or conventions: e.g. single user data dir, SQLite path under Config port, service supervised by Electron on desktop start, backup left to user/OS — **or** one AD “Local deployment envelope” binding data dir + loopback port + token file layout.

- **medium** Observability / support diagnostics not named — NFR-3 implies visible errors; no convention for structured service logs vs UI logs. Low stakes but can diverge in multi-adapter debugging. *Fix:* One convention row: “Correlation id per lesson session in API logs and stream events.”

---

## Summary table (severity)

| Severity | Count | Themes |
| --- | ---: | --- |
| critical | 0 | — |
| high | 3 | Local API transport fork (AD-3); SSE/WebSocket deferred fork (AD-5/Deferred); operational envelope thin |
| medium | 7 | SRS/plans PRD deferral; scheduler port; FR-4 summary binding; AD-5 enforceability; NFR-2 map; SQLite migrations; observability |
| low | 4 | Unpinned stack policy; Python 3.11 hint; AD-4 mechanical enforcement; SM not mapped |

---

## Recommended fix order (for Finalize / Update)

1. **Lock local wire contracts** — Resolve AD-3 transport and AD-5 stream protocol (or add hard gate before parallel epics).
2. **State v1 SRS stance** — Explicit defer or minimal AD so persistence + Telegram micro-lessons share one model.
3. **Envelope one-pager** — Data dir, service lifecycle supervision, config/token files (decide or defer with invariants).
4. **Capability map** — Add NFR-2 row; optional scheduler AD/defer.
5. **Polish** — FR-4 template summary convention; migration ownership deferral.

---

## Artifacts referenced

- `ARCHITECTURE-SPINE.md` (review target)
- `_bmad-output/planning-artifacts/prds/prd-ai-language-teacher-2026-09-22/prd.md`
- `_bmad-output/planning-artifacts/prds/prd-ai-language-teacher-2026-09-22/addendum.md`
- `.memlog.md` (same architecture folder)
