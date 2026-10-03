---
epic: 1
date: 2026-09-28
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Epic 1 Retrospective — Desktop teacher foundation

## Epic summary

- **Epic:** 1 — Desktop teacher foundation
- **Goal:** Runnable personal-desktop substrate (Electron+Vue + Python teacher on loopback HTTP; Config/secrets/SQLite; branded Russian chrome; empty calendar; Settings shells with LLM/API explicit save; window-close must not stop teacher).
- **Diff range:** `74ee1e4^..14374ae` (first story commit `74ee1e4 feat(scaffold)…` through merge of PR #16 / 1.6 review patches).
- **Stories completed (6/6, `pending_stories: []`):**
  - `1-1-scaffold-electron-vue-desktop-and-python-teacher-package`
  - `1-2-loopback-http-api-with-local-auth-and-electron-service-lifec`
  - `1-3-config-port-secrets-layout-and-sqlite-app-data-store`
  - `1-4-design-tokens-dark-mode-and-russian-app-chrome-shell`
  - `1-5-calendar-home-empty-chrome-with-side-panel`
  - `1-6-settings-sections-shell-with-explicit-save`
- **Sprint:** `epic-1: done`; `epic-1-retrospective: done` (this run); 5 open action items appended.
- **Acceptance criteria:** Declared in `_bmad-output/planning-artifacts/epics.md` (Epic 1 + per-story ACs) and `_bmad-output/implementation-artifacts/epic-1-context.md`.

### Evidence inventory

| Artifact                          | Status        | Source                                                                                                                                           |
| --------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Epic spec / ACs                   | Available     | `epics.md` Epic 1; `epic-1-context.md`                                                                                                           |
| Story specs                       | Available (6) | `spec-1-1` … `spec-1-6` under `implementation-artifacts/`                                                                                        |
| Diff + commits                    | Available     | `git_evidence.py` on `74ee1e4^..14374ae`: 29 commits, 13 merges (12 measured), 117 paths in `files`                                              |
| Per-story commit auto-attribution | Weak          | Only merge `#15` subject matched a full story id; conventional subjects use `1.N` / feature words — map below is manual from PR/subject evidence |
| Sprint status                     | Available     | `sprint-status.yaml`                                                                                                                             |
| Previous retrospective            | Absent        | No prior epic retro — follow-through N/A                                                                                                         |
| Session logs                      | Partial       | Late Epic 1 transcripts (1-6 review / retro); earlier story sessions not systematically retained — process-lesson analysis narrowed              |
| Deferred ledger                   | Available     | `deferred-work.md` (open + `resolved_by` entries across 1.1–1.6)                                                                                 |

### Manual per-story commit map

| Story      | Representative commits                                  |
| ---------- | ------------------------------------------------------- |
| 1.1        | `74ee1e4`, `b21b36f`, `174d80f`, merge `#6` `a88e2ed`   |
| 1.2        | `fc787ca`, `94ae270`, merges `#7`/`#8`                  |
| 1.3        | `cf9f63d`, `c95cc1e`, merges `#9`/`#10`                 |
| 1.4        | `a311c80`, `66a774c`, merges `#11`/`#12`                |
| 1.5        | `5191f70`, merge `#13`                                  |
| 1.6        | `412f108`, `bf7be1e`, merges `#15`/`#16`                |
| Supporting | Devcontainer GUI / `.env` (`58406f2`, `a88de8d`, `#14`) |

### Top code churn (`git_evidence.py` `files`, non-merge)

Excluding lockfiles: `CalendarHome.vue` (+501), `SettingsView.vue` (+438), `SettingsView.spec.ts` (+424), `teacherHost.ts` (+419), `teacherHost.spec.ts` (+411), `test_config_persistence.py` (+366), `App.spec.ts` (+320).

### Phase status

- [x] Phase 1 — Gather
- [x] Phase 2 — Analyze
- [x] Phase 3 — Team Discussion (party mode)
- [x] Phase 4 — Decide
- [x] Phase 5 — Finalize

## Findings

Dispositions human-confirmed in Phase 4. Sub-agent reports were re-checked against primary sources before routing.

### Aggregate views

| ID    | View           | Disposition | Source                                                    | Finding                                                                                                                        |
| ----- | -------------- | ----------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| A1    | architecture   | accept      | `domain/learner.py`; rg domain for SDK imports = none     | Hexagonal domain clean — no Vue/Electron/Telegram/LLM SDK imports.                                                             |
| A2    | architecture   | accept      | `ipcChannels.ts`, `preload/index.ts`, `index.ts:126-132`  | IPC lifecycle-only (`get-auth` / `retry` / `status`); domain traffic is HTTP.                                                  |
| A3    | architecture   | accept      | `index.ts:139-153`, `hostSurvival.ts`, `412f108`          | Window-close → hide; teacher stop only on quit of owned child — HOST_SURVIVAL landed.                                          |
| A4    | architecture   | defer       | `teacherHost.ts:37-69` vs `layout.py:36-46`               | Dual data-dir resolvers (manual Node paths vs Python `platformdirs`) — drift risk across attach/spawn.                         |
| D1    | duplication    | defer       | `teacherHost.ts`, `preload/index.ts`, `teacherClient.ts`  | `TeacherStatus` shape triplicated across main/preload/renderer.                                                                |
| G1–G2 | god-class      | accept      | `CalendarHome.vue` 501, `SettingsView.vue` 438            | Large but cohesive SFCs (calendar CSS-heavy; Settings shell + LLM save).                                                       |
| G3    | god-class      | defer       | `teacherHost.ts` 419                                      | Borderline multi-concern host (layout + bearer + spawn + health) — candidate future split, not a layering leak.                |
| P2    | patterns       | fix now     | `ThemeControl.vue:6-14` vs `App.vue` Russian nav          | Theme labels English (`System`/`Light`/`Dark`) while chrome is Russian (UX-DR20).                                              |
| P1    | patterns       | accept      | Calendar vs Settings quote style                          | Quote/semicolon style split across stories — cosmetic.                                                                         |
| S1    | reconciliation | fix now     | `AGENTS.md:37`; deferred-work L80; as-built `teacherHost` | AGENTS still claims Electron spawn/attach/host-survival **remain deferred** after they shipped in 1.6.                         |
| S2    | reconciliation | defer       | `epics.md:226-228`; deferred-work L45-47; `app.py` routes | Story 1.3 learner/profile (or config-status) HTTP projection never shipped — only `/health` + `/config/llm`. Already ledgered. |
| S3–S4 | reconciliation | accept      | deferred-work `resolved_by` → 1.5/1.6                     | Host-survival, auth bridge, remint, Russian shell, Settings LAUNCH_FAILURE_UI landed as deferred resolutions.                  |
| S5    | reconciliation | defer       | deferred-work L21-23                                      | Polished **global** teacher status chrome still deferred (Settings banner only).                                               |
| S8    | reconciliation | defer       | deferred-work L31-32, L49-51                              | AGENTS unauth health body assert + Config bearer bootstrap docs still parked (agent-context).                                  |

### Diff-scope review (`bmad-review` lenses on `/tmp/epic1-src.diff`)

#### Cross-story / runtime seams (re-verified)

| ID  | Lens               | Disposition                        | Source                                                                                                                              | Finding                                                                                                                                                                                       |
| --- | ------------------ | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R1  | adversarial + edge | **fix now**                        | `renderer/index.html:5-8` CSP `default-src 'self'` (no `connect-src` for `:8765`); `webPreferences` leaves `webSecurity` default on | Renderer `fetch` to loopback teacher is likely blocked by CSP in both Vite-dev and packaged loads. Unit tests mock HTTP — would not catch. **Settings LLM save AC may fail at real runtime.** |
| R2  | adversarial        | **fix now** (CORS — human chose A) | `app.py` — no `CORSMiddleware` / OPTIONS exemption (rg CORS = none)                                                                 | Cross-origin Vue origin → `127.0.0.1:8765` needs CORS (chosen) not main-process proxy. Same seam as R1.                                                                                       |
| R3  | adversarial        | defer                              | `index.ts` — no `requestSingleInstanceLock`                                                                                         | Second app instance → second tray + TeacherHost on fixed `:8765`.                                                                                                                             |
| R4  | adversarial + edge | defer                              | `teacherHost` spawn/kill                                                                                                            | `uv run` child kill may orphan Python on port; attach 401 path has no reclaim/remint.                                                                                                         |
| R5  | adversarial        | defer                              | `teacherHost.ts:84-94` vs `layout.py` atomic write                                                                                  | Node bearer write is non-atomic / no symlink guard; Python uses mkstemp+replace + symlink reject.                                                                                             |
| R6  | adversarial        | defer                              | `auth.py` env-over-Config vs host Config-as-authority                                                                               | Precedence mismatch risk when shell `TEACHER_AUTH_TOKEN` differs from file.                                                                                                                   |
| R7  | edge (claim)       | defer                              | `index.ts:139-154`                                                                                                                  | “Tray-only quit” narrative vs `before-quit` stopping owned teacher on any `app.quit()` (incl. Cmd+Q).                                                                                         |
| R8  | edge (claim)       | defer                              | `SettingsView.vue:164-174`                                                                                                          | Unsaved discard confirm is route-leave only — quit/destroy skips confirm.                                                                                                                     |
| R9  | adversarial        | accept (later epic)                | `learner.py` timezone UTC vs calendar local `Date`                                                                                  | Documented for Epic 2 schedule wiring; empty chrome today is local-only.                                                                                                                      |
| R10 | adversarial        | defer                              | `sqlite.py` create_learner race                                                                                                     | Concurrent get-or-create can dual-insert; low risk until multi-caller HTTP.                                                                                                                   |

#### Verification gaps

| ID  | Lens             | Disposition    | Source                                          | Finding                                                                                        |
| --- | ---------------- | -------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| V1  | verification-gap | defer          | deferred-work + `hostSurvival.spec.ts`          | HOST_SURVIVAL wiring in `index.ts` untested (helpers only).                                    |
| V2  | verification-gap | defer          | deferred-work + preload never imported in specs | AUTH_BRIDGE IPC path untested end-to-end.                                                      |
| V3  | verification-gap | defer          | deferred-work + `main.ts` vs `App.spec`         | Production router `.use(createAppRouter())` not executed by vitest.                            |
| V4  | verification-gap | defer          | deferred-work                                   | `teacher-api` console-script / `__main__` resolution not asserted in pytest.                   |
| V5  | verification-gap | fix now (test) | `teacherHost.spec.ts` checkHealth               | Health probes never assert `Authorization: Bearer …` header — weak attach/spawn auth contract. |
| V6  | verification-gap | defer (new)    | Node vs Python data-dir tests                   | No cross-stack parity test for shared Config layout / bearer round-trip.                       |
| V7  | verification-gap | defer          | `index.ts` navigation allowlist                 | `isAllowedDevRendererUrl` / will-navigate untested; file:// allow is broad.                    |
| V8  | verification-gap | defer          | `teacherClient.spec.ts`                         | `retryTeacher` missing-bridge path uncovered (getTeacherAuth covered).                         |

### Process lessons (narrowed — session logs partial)

- Story splits into deferred-work + later `resolved_by` worked for 1.2→1.6 and 1.4→1.5, but left **AGENTS.md** and **epics.md** ACs without cross-links (S1, S2, S8).
- Conventional commit subjects rarely carry full story slugs → `git_evidence.py` auto-attribution nearly empty; process: include story id in merge/PR titles or subjects.
- Epic-spanning seams (CSP/CORS for renderer→teacher) were never owned by a single story.

## Behavior verification

| Check                                      | Result                                                                                                                     | Source                                                                                            |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `uv run pytest` (teacher)                  | **50 passed**                                                                                                              | this run                                                                                          |
| `npm test` (desktop)                       | **78 passed** (7 files)                                                                                                    | this run                                                                                          |
| Teacher HTTP smoke                         | `GET /health` → `{"status":"ok"}`; unauth → `401` + `{code,message,retryable}`; `GET /config/llm` → `{"configured":false}` | temp `TEACHER_DATA_DIR` + `TEACHER_AUTH_TOKEN`                                                    |
| Electron GUI / Settings→teacher live fetch | **Not exercised**                                                                                                          | CSP/CORS (R1/R2) therefore remain open runtime risks; unit suites mock `fetch` / `window.teacher` |
| Host-survival tray close                   | **Not exercised** in GUI                                                                                                   | Covered only by pure `hostSurvival` helpers + code inspection                                     |

## Previous-retro follow-through

No prior epic retrospective document and no `action_items` from an earlier retro in `sprint-status.yaml`. Nothing to follow through on.

## Phase 3 — Team discussion

Party mode (`installed` roster; substantive voices: John, Murat, Amelia, Winston). Seeded with Phase 2 findings only.

- **John:** `accepted-with-open-items` valid iff R1/R2 are sprint blockers for Settings LLM save — not cosmetics.
- **Murat:** Unit/smoke green ≠ live Settings; wanted stronger gate until GUI or CSP/CORS closed; accepted documenting _runtime Settings unverified_.
- **Amelia:** Sprint order — CSP+CORS → Bearer `checkHealth` assert → AGENTS → Theme RU.
- **Winston:** Prefer **CORS + CSP** over main-process HTTP proxy to keep Electron thin-host / loopback HTTP topology (AD-3).

User decisions after discussion: verdict **accepted-with-open-items**; HTTP seam fix = **option A (CORS + CSP)**.

## Action items

Human-confirmed for sprint (`status: open` via Phase 5 `sprint_status.py update`).

| #   | Kind                | Owner | Action                                                                                                                                                                                                        | From              |
| --- | ------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| 1   | Remediation         | Dev   | Fix Settings↔teacher HTTP: CSP `connect-src` for loopback `:8765` **and** CORS on teacher (OPTIONS exempt from Bearer; tight Origin/`null` allowlist). Do **not** proxy domain traffic through Electron main. | R1, R2; Winston A |
| 2   | Spec reconciliation | Dev   | Update `AGENTS.md` Running section: spawn/attach/preload/host-survival **shipped** in 1.6; keep learner/profile projection marked deferred                                                                    | S1, S8            |
| 3   | Remediation         | Dev   | Localize `ThemeControl` labels to Russian (UX-DR20)                                                                                                                                                           | P2                |
| 4   | Remediation         | Dev   | Assert Bearer header in `teacherHost` `checkHealth` / attach-spawn health tests                                                                                                                               | V5                |
| 5   | Process             | Team  | Prefer story id in commit/PR subjects for evidence scripts; assign cross-cutting wire seams (CSP/CORS) to an explicit story AC in later epics                                                                 | process           |

Deferred (remain in `deferred-work.md`, not duplicated as sprint remediations): learner/profile HTTP (S2); Electron harness HOST_SURVIVAL/AUTH_BRIDGE (V1–V2); entrypoint resolve (V4); Node↔Python layout parity (V6); single-instance lock (R3); process-group kill (R4); atomic bearer write parity (R5); polished global status chrome (S5).

## Acceptance verdict

- **Criteria:** declared (`epics.md` Epic 1 + `epic-1-context.md`).
- **Stories:** all `done` (`pending_stories: []`).
- **Verdict:** **accepted-with-open-items** (human confirmed 2026-09-28).
- **Evidence:** substrate shipped (scaffold, loopback Bearer API, Config/SQLite, tokens/chrome, calendar empty chrome, Settings shells + LLM save path, host-survival wiring); pytest 50 + vitest 78; HTTP smoke `/health` + 401 shape + `/config/llm`. Named open items tracked as action items 1–5 and deferred-work ledger. Live Electron Settings→teacher fetch still unverified pending item 1.

## Open questions

None blocking finalize. Live GUI confirmation of Settings save remains desirable after action item 1 lands.
