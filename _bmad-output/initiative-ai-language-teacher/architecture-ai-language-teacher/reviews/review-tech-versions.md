# Technology & Version Reality Check — ARCHITECTURE-SPINE.md

**Artifact:** `_bmad-output/planning-artifacts/architecture/architecture-ai-language-teacher-2026-09-23/ARCHITECTURE-SPINE.md`  
**Lens:** Verify committed stack decisions against live web/registry reality (not training-data assertions); greenfield starter defaults; mechanical vs semantic pin policy.  
**Date:** 2026-09-23  
**Spine status:** `draft`  
**Project reality:** Greenfield — no `apps/` or `services/` product tree; planning artifacts only (confirmed via repo layout and memlog line 14).

---

## Verdict

**Conditional pass — families fit; provenance gap.**

Every **named stack family** (Electron, Vue 3, Vite, Python, FastAPI, LangGraph, SQLite) **still exists**, is **actively maintained**, and **matches** a local desktop client + loopback teacher service + lesson event stream + in-phase LLM orchestration. Deferring exact semver pins to first scaffold is **acceptable for this draft** and **passes mechanical `lint_spine.py`** (non-empty Version cells). It does **not** satisfy the architecture skill’s stronger expectation that bindings be **web-verified at authoring** — the spine and memlog contain **no version research trail**, and the Stack section omits the template’s “verified current at authoring” provenance comment.

**Not a mechanical lint failure.** **Is a semantic / finalize-readiness gap** until scaffold pins land or the Stack block records verification date + reference versions.

---

## Mechanical gate: deferred pins

| Check | Result |
| ----- | ------ |
| `lint_spine.py --workspace {doc_workspace}` | `ok: true`, 0 findings |
| Stack rows use `pin at scaffold` | Treated as **pinned** (non-blank, non-`{token}`) |
| Empty / `{pin}` version cells | Would fail `version_pin` (medium) — **not present** |

**Judgment:** Explicit deferral in Stack + Deferred table is **consistent** with greenfield `status: draft` and rubric walker’s “low divergence risk” for version pins **if** a single scaffold epic owns all pins. For **finalize**, expect real semver in the Stack table or a bound AD-amendment that copies lockfiles into the spine.

---

## Live registry snapshot (verified 2026-09-23)

Sources: PyPI JSON API, npm registry (`latest`), prior web search cross-check. Use as **reference bands** for scaffold — not spine commitments.

| Family | Latest stable (checked) | Exists & active | Fit for v1 topology |
| ------ | ---------------------- | ----------------- | ------------------- |
| **Electron** | **44.4.5** (npm; releases site also lists 44.x / Chromium 152 / bundled Node ~24) | Yes | Thin window host + separate Python process — standard pattern |
| **Vue 3** | **3.5.43** (npm; 3.6.x RC only on minor branch) | Yes | Renderer for lesson UI; stable 3.5 line appropriate |
| **Vite** | **8.3.0** (npm, 2026-09-10) | Yes | Pairs with electron-vite; Node engine 20.19+ / 22.12+ — compatible with Electron 44’s bundled Node |
| **electron-vite** (implied, not named in spine) | **5.0.0** (npm) | Yes | De facto scaffold for Electron + Vite + Vue |
| **@quick-start/create-electron** | **1.0.30** (npm) | Yes | Official CLI: `npm create @quick-start/electron@latest -- --template vue-ts` |
| **Python 3** | 3.12–3.13 production baseline; 3.14 gaining LangGraph CI/classifier support | Yes | Teacher service runtime |
| **FastAPI** | **0.141.1** (PyPI) | Yes | Loopback ASGI API; **native SSE** since **0.135.0** (`fastapi.sse.EventSourceResponse`) — strong fit for AD-5 |
| **LangGraph** | **1.2.12** (PyPI; 1.2.x line) | Yes | In-phase agent loops per AD-8; requires **langchain-core** (transitive — not listed in Stack) |
| **SQLite** | stdlib `sqlite3` + ecosystem (SQLAlchemy, etc.) | Yes | Single-user local store per AD-7 |
| **langgraph-checkpoint-sqlite** | **3.1.1** (PyPI; aligned with LangGraph 1.2.x releases) | Yes | Optional **graph checkpoint** store — distinct from domain SQLite in AD-8 (graph must not write plan/session DB directly) |

**LLM / Voice rows:** Correctly scoped as port-bound, not pinned offline stacks — no version lint expected.

---

## Findings (tiered)

### High — no documented web verification in the artifact

**What:** Memlog (`.memlog.md`) records PRD/brief-driven `(decision)` and `(constraint)` lines but **no `(version)` or research entries**. Stack header says `SEED — families adopted; exact version pins deferred` but **not** “verified current at authoring” per `spine-template.md`.

**Why it matters:** `bmad-architecture` SKILL.md: *“Verify any named technology's current version and fit on the web before binding it.”* Family names **are** bindings for implementers choosing starters and CI images.

**Risk:** Teams scaffold from stale mental models (e.g. Vite 5/6, LangGraph 0.x, sse-starlette-only FastAPI).

**Fix (autofix-friendly):** On finalize or at scaffold, append memlog `(version)` lines and add Stack HTML comment, e.g. `<!-- SEED — families verified 2026-09-23; pins applied at scaffold -->`, plus semver rows from lockfiles.

---

### High — greenfield starter implied but not named; folder seed may diverge from live defaults

**What:** Stack lists Electron + Vue 3 + Vite but **does not name** `electron-vite` or `create-electron`. Structural seed uses:

```text
apps/desktop/   # Electron main + Vue renderer
```

**Live starter defaults** (electron-vite docs, 2025–2026):

- Recommended layout: `src/main`, `src/preload`, `src/renderer`, `electron.vite.config.ts`
- Legacy/alternate: `electron/main`, `electron/preload`, repo-root `src` + `vite.config.ts` (electron-vite-vue boilerplate)
- **Security default:** no `nodeIntegration` in renderer; preload + `contextBridge` for capability exposure
- Scaffold command: `npm create @quick-start/electron@latest my-app -- --template vue-ts`

**Clash with AD-3 / AD-11:** Starters often teach **Electron IPC** for renderer↔main. Spine mandates **HTTP (or undecided IPC) to Python teacher** — not documented as a deliberate deviation from starter docs. Implementers may wire domain calls through preload IPC while Telegram uses HTTP, reviving the fork rubric walker flagged.

**Fix:** Add Deferred or Stack note: “Desktop scaffold: `@quick-start/electron` vue-ts; map `apps/desktop/` to electron-vite layout at init; domain traffic only to loopback FastAPI.” Record in scaffold epic.

---

### Medium — LangChain ecosystem dependency invisible in Stack

**What:** LangGraph 1.2.x **depends on langchain-core** (and related packages). Stack names LangGraph only.

**Risk:** Python service lockfile surprises; security/license review misses chain packages; version skew between `langgraph` and `langchain-core` breaks at runtime.

**Fix:** Stack row or Deferred: “LangGraph stack pins include langchain-core (and checkpoint lib if used) at scaffold.” Optional: `langgraph-checkpoint-sqlite` if graph checkpoints are file-backed separately from domain DB — still subject to AD-8 (domain owns lesson session persist).

---

### Medium — Python major left open; recommend explicit floor at scaffold

**What:** “Python 3 — pin at scaffold” with no floor.

**Live reality:** FastAPI ≥3.10; LangGraph ≥3.10; production guides commonly **3.12**; LangGraph adding **3.14** CI/classifiers (2026).

**Fit:** 3.12 or 3.13 is a safe v1 target; 3.14 only after dependency matrix check.

**Fix:** Convention or Stack note: “Python ≥3.12 at scaffold” (or chosen pin).

---

### Medium — AD-5 stream transport deferred; FastAPI capability not reflected in spine

**What:** AD-5 and Deferred leave SSE vs WebSocket open.

**Reality check:** FastAPI **0.141.1** ships first-class SSE (`EventSourceResponse`, `ServerSentEvent`, reconnection via `Last-Event-ID`). Browser `EventSource` is GET-only; POST SSE exists in FastAPI but needs non-EventSource client — relevant if auth headers differ.

**Judgment:** Deferral is **product-valid** but **misses a free, verified-default** that reduces parallel-epic divergence. Not stale tech — **stale decision opportunity**.

**Fix:** Prefer SSE in AD-5 Rule or document “default SSE unless WebSocket required” when pins ≥ FastAPI 0.135.

---

### Low — SQLite “stdlib/SQLAlchemy or equivalent”

**What:** Appropriate deferral. SQLAlchemy 2.x is current standard; stdlib-only viable for minimal adapters.

**Reality:** No conflict with AD-7. Migrations still undeferred (rubric walker).

---

### Low — Electron major drift vs blog templates

**What:** Community monorepo templates may lag (e.g. “Electron 40” README vs npm **44.x**). **Always pin from `npm install electron@latest` at scaffold**, not from third-party boilerplate badges.

---

## Named-family fit summary (local desktop teacher)

| Concern | Assessment |
| ------- | ---------- |
| Desktop UI + background Python service | Electron + separate FastAPI process matches AD-2 |
| Loopback API + bearer token | FastAPI + Starlette middleware — mainstream |
| Lesson event stream | FastAPI SSE native; WebSocket via Starlette still valid |
| In-phase LLM loops | LangGraph 1.2.x is current product line (not legacy 0.x) |
| Single-user persistence | SQLite appropriate; LangGraph SQLite checkpoint is adjunct, not replacement for domain schema |
| Telegram + scheduler in Python | Independent of JS stack versions |
| Voice local-first | Port deferral correct; no stack pin needed yet |

**No dead or renamed technologies detected** in the Stack table.

---

## Brownfield ratification

N/A — greenfield. Spine does not contradict existing application code (none present).

---

## Recommendations (prioritized)

1. **At scaffold (blocking for parallel client/service epics):** Pin all Stack rows from lockfiles; add memlog `(version)` lines; run `lint_spine.py` again (should remain clean with semver cells).
2. **Before desktop epic:** Name starter (`create-electron` vue-ts) and map `apps/desktop/` to electron-vite layout; state “no domain IPC” in AD-3 amendment.
3. **Stack completeness:** Add langchain-core (and optional checkpoint package) to Python dependency family or Deferred caveat.
4. **Optional quick win:** Default SSE in AD-5 backed by FastAPI ≥0.135 pin at scaffold.
5. **Finalize polish:** Restore template provenance comment on Stack when versions are known.

---

## Evidence log (this review)

| Action | Source |
| ------ | ------ |
| PyPI latest | `https://pypi.org/pypi/fastapi/json`, `langgraph/json` |
| npm latest | `electron`, `vue`, `vite`, `electron-vite`, `@quick-start/create-electron` |
| Mechanical lint | `python .agents/skills/bmad-architecture/scripts/lint_spine.py --workspace …` → ok |
| Memlog / spine read | `.memlog.md`, `ARCHITECTURE-SPINE.md` |
| Starter docs | electron-vite.org guide (web search); GitHub electron-vite/electron-vite-vue |
| FastAPI SSE | fastapi.tiangolo.com tutorial/reference (web search); release ≥0.135.0 |
| LangGraph SQLite checkpoint | PyPI `langgraph-checkpoint-sqlite` 3.1.1; LangGraph docs |

---

## Compact summary (for gate rollup)

**Verdict:** Conditional pass — families fit; document verification at scaffold/finalize.  
**Top findings:** (1) No web-verification provenance in memlog/spine vs skill requirement. (2) Implied electron-vite starter not named; `apps/desktop/` vs official layout/IPC defaults. (3) LangGraph implies langchain-core missing from Stack. (4) Python floor unset — recommend ≥3.12. (5) FastAPI 0.141 + native SSE supports AD-5 but spine still defers transport.
