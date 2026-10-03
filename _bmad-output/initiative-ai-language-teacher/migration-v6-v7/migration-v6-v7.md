---
type: migration
title: "Move v6 planning and implementation artifacts into the v7 initiative layout"
status: done
created: 2026-10-03
from: "6"
to: "7"
module: method
---

# Migration v6 → v7 — ai-language-teacher

## Detect signals matched

- `planning-artifacts/epics.md` present
- `implementation-artifacts/sprint-status.yaml` present
- Classic build records `spec-<epic>-<story>-<slug>.md` with `route:` + `status:` frontmatter
- Dated planning folders: `prds/prd-…-2026-09-22/`, `briefs/brief-…-2026-09-22/`, `ux-designs/ux-…-2026-09-22/`, `architecture/architecture-…-2026-09-23/`
- `specs/spec-ai-language-teacher/SPEC.md` (+ companions; `stories.yaml` present, **no** `stories/` folder)
- No `core.active_initiative` in `_bmad/custom/config.user.toml`
- No `initiative-*/` folder under `_bmad-output/`

Source folders (from `_bmad/config.toml` defaults; no custom path overrides):

| Role           | Path                                     |
| -------------- | ---------------------------------------- |
| output         | `_bmad-output/`                          |
| planning       | `_bmad-output/planning-artifacts/`       |
| implementation | `_bmad-output/initiative-ai-language-teacher/` |

## Inventory summary

| Area                                    | Contents                                                                                                                                                                                         |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Tracking                                | `epics.md` (4 epics, 29 stories); `sprint-status.yaml` (epic-1 done; epic-2 in-progress; epic-3/4 backlog); all `action_items` **done**                                                          |
| Build records (matched)                 | Epic 1: 1.1–1.6 done plans; Epic 2: 2.1 onboarding, 2.2, 2.3 placement, 2.4 done plans                                                                                                           |
| Build records (no matching `### Story`) | `spec-2-1-outlook-week-grid-schedule.md`, `spec-2-3-listening-player-scrub-seek-replay.md`, `spec-2-3-cloud-voice-fallback.md` — all `status: done` (flagged as extra entries 8–10 under epic 2) |
| Caches / retro                          | `epic-1-context.md`, `epic-2-context.md` → archive; `epic-1-retro-2026-09-28.md` → `epic-desktop-teacher-foundation/epic-desktop-teacher-foundation-retrospective.md`                            |
| Deferred                                | `deferred-work.md` → initiative root (paths rewritten after moves)                                                                                                                               |
| Planning docs                           | brief, prd (+ reviews/addenda), architecture (+ reviews/html), ux (DESIGN/EXPERIENCE/mockups/wireframes/imports/`.working`/validation)                                                           |
| Spec                                    | `spec-ai-language-teacher/` — **planning document only** (has `stories.yaml` but **no** `stories/`; do not invent a fifth epic from CAP story breakdown)                                         |
| Remnant                                 | `party-mode/memories/installed/.memlog.md` → `inbox/` (unrelated memlog)                                                                                                                         |

No stories currently `in-progress` or `review`/`in-review`. Epic 2 is `in-progress` with 2.5–2.7 still `backlog` (no build files yet). Finish-first question is therefore **N/A — migrate now**.

## Proposed initiative

One initiative: `initiative-ai-language-teacher` (from `core.project_name`).

Target tree (after approval):

```text
_bmad-output/
  initiative-ai-language-teacher/
    initiative-ai-language-teacher.md
    tickets.toml
    deferred-work.md
    prd-ai-language-teacher/…
    brief-ai-language-teacher/…
    ux-ai-language-teacher/… (+ ux-ai-language-teacher.md router)
    architecture-ai-language-teacher/…
    spec-ai-language-teacher/… (+ stories.yaml as companion; archived copy of stories.yaml? keep as companion)
    epic-desktop-teacher-foundation/
    epic-first-run-onboarding-living-plan-on-calendar/
    epic-live-voice-lessons/
    epic-telegram-cadence-progress-replan/
    archive-v6/   # epics.md, sprint-status.yaml, epic-*-context.md
    migration-v6-v7/migration-v6-v7.md   # this plan, moved in
  inbox/
    space.md
    archive-v6/   # or party-mode tree as-is
      party-mode/…   # moved as it was
```

Epic folder slugs (from titles, no numbers):

| v6                                                     | v7 slug                                             | status                     |
| ------------------------------------------------------ | --------------------------------------------------- | -------------------------- |
| Epic 1: Desktop teacher foundation                     | `epic-desktop-teacher-foundation`                   | done                       |
| Epic 2: First-run onboarding & Living plan on calendar | `epic-first-run-onboarding-living-plan-on-calendar` | in-progress                |
| Epic 3: Live voice lessons                             | `epic-live-voice-lessons`                           | (backlog — no status line) |
| Epic 4: Telegram cadence, Progress & replan            | `epic-telegram-cadence-progress-replan`             | (backlog — no status line) |

Epic `after`: Epic 2 needs Epic 1 foundation; Epic 3 needs Epic 2 onboarding/plan; Epic 4 needs Epic 3 lessons (and Telegram after Settings shell from 1). Recorded as `after = [{ epic = N, needs = "…" }]` on initiative `tickets.toml`.

## Four lists (correct once)

### Joins the initiative

| File / folder                                                 | Evidence                                      |
| ------------------------------------------------------------- | --------------------------------------------- |
| `prds/prd-ai-language-teacher-2026-09-22/**`                  | `epics.md` inputDocuments; SPEC sources       |
| `briefs/brief-ai-language-teacher-2026-09-22/**`              | PRD builds on brief                           |
| `architecture/architecture-ai-language-teacher-2026-09-23/**` | `epics.md` inputDocuments; SPEC companions    |
| `ux-designs/ux-ai-language-teacher-2026-09-22/**`             | `epics.md` inputDocuments; SPEC companions    |
| `specs/spec-ai-language-teacher/**`                           | `epics.md` inputDocuments; canonical contract |
| All matched `spec-N-M-*.md` + three extra done specs          | Sprint + epic stories / flagged extras        |
| `deferred-work.md`                                            | Implementation tracking companion             |
| `epic-1-retro-2026-09-28.md`                                  | Epic 1 retrospective (done)                   |
| `epics.md`, `sprint-status.yaml`, `epic-*-context.md`         | Archive under initiative                      |

### Moves to inbox (default yes)

| Path          | Reason                                                           |
| ------------- | ---------------------------------------------------------------- |
| `party-mode/` | Unrelated party-mode memlog remnant; not cited by PRD/epics/spec |

### Stays where it is

None planned at store root after migration (empty v6 folders removed).

### Archived (under initiative `archive-v6/`)

- `epics.md`
- `sprint-status.yaml`
- `epic-1-context.md`, `epic-2-context.md`
- Folded unstarted story files: **none** (2.5–2.7 / epic 3–4 have no build records)

## Ticket tree (planned)

### Initiative covers

`CAP-1`…`CAP-15` from SPEC (requirement source at initiative altitude). PRD FR1–FR15 map to those CAP ids via existing coverage.

### Epic 1 — Desktop teacher foundation (`done`)

Covers: (none in FR map — enables substrate; cite NFR4 / AD / UX-DR in Requirements lines). Entries 1–6 from Stories 1.1–1.6; each gets `story-<slug>-plan.md` with `status: done`, `type: feature`, keep existing `baseline_commit` as `baseline_revision` when present.

### Epic 2 — First-run onboarding… (`in-progress`)

Covers: FR1/CAP-1, FR2/CAP-2, FR3/CAP-3 (+ FR4 Living plan surface note for 2.5).

| id  | title                                                              | v6_key / note                            | plan                |
| --- | ------------------------------------------------------------------ | ---------------------------------------- | ------------------- |
| 1   | Onboarding wizard — greeting, goals, interests, duration, schedule | `2-1-onboarding-…`                       | done plan           |
| 2   | Consent and regulated copy gating                                  | `2-2-…`                                  | done plan           |
| 3   | Placement — briefing, written, listening, speaking                 | `2-3-placement-…`                        | done plan           |
| 4   | Living plan creation and persistence                               | `2-4-…`                                  | done plan           |
| 5   | Living plan full-screen document (view-only)                       | `2-5-…` backlog                          | entry only          |
| 6   | Calendar climax — scheduled events…                                | `2-6-…` backlog                          | entry only          |
| 7   | Settings wiring — Voice, Schedule edit, Goals                      | `2-7-…` backlog                          | entry only          |
| 8   | Outlook week-grid schedule UI                                      | **no matching Story** — extra done build | done plan (flagged) |
| 9   | Listening player — scrub, seek, replay                             | **no matching Story** — follow-on to 2.3 | done plan (flagged) |
| 10  | Cloud Voice fallback behind VoicePort (AD-9)                       | **no matching Story** — AD-9 work        | done plan (flagged) |

### Epic 3 — Live voice lessons (backlog)

Covers: FR4, FR6–FR11 / CAP-4, CAP-6–CAP-11. Entries 1–10 from Stories 3.1–3.10; **entry only** (no plans).

### Epic 4 — Telegram cadence, Progress & replan (backlog)

Covers: FR5, FR12–FR15 / CAP-5, CAP-12–CAP-15. Entries 1–6 from Stories 4.1–4.6; **entry only**.

### Action items

All sprint `action_items` are `done` → dropped (not copied into initiative Notes).

## Path rewrites (in-store)

Rewrite live references from old paths to new initiative-relative paths in:

- SPEC `companions:` / `sources:`
- epics archive left unchanged; live initiative/epic/plan References and deferred-work `source_spec` lines
- UX/architecture relative links recomputed after `git mv`

### Outside-store references (list only — user updates)

| File                               | Notes                                                    |
| ---------------------------------- | -------------------------------------------------------- |
| `AGENTS.md`                        | Points at `_bmad-output/specs/…`, architecture, UX paths |
| Possibly docs / comments elsewhere | Will re-scan at execute; report full list                |

Do **not** edit those during migration.

## Configuration (on approval)

Create `_bmad/custom/config.user.toml`:

```toml
[core]
active_initiative = "initiative-ai-language-teacher"
```

Leave installer `_bmad/config.toml` and `planning_artifacts` / `implementation_artifacts` alone. No workspace / separate store repo unless you answer yes below.

## Questions

| #   | Question                                                                                 | Default                              | Answer                                                    | Reason                   |
| --- | ---------------------------------------------------------------------------------------- | ------------------------------------ | --------------------------------------------------------- | ------------------------ |
| 1   | Back up `_bmad-output` to `_bmad-output-bak` first? (clean committed git already counts) | Yes                                  | **Git counts as backup** (no folder copy)                 | User: all defaults       |
| 2   | One initiative or several, and names?                                                    | One, named after `core.project_name` | **One:** `initiative-ai-language-teacher`                 | User: all defaults       |
| 3   | Will this work touch other repositories? (`workspace`)                                   | No                                   | **No**                                                    | User: all defaults       |
| 4   | Keep planning files' git history in their own repository?                                | No                                   | **No**                                                    | User: all defaults       |
| 5   | In-progress/review stories: finish in v6 first, or migrate now?                          | Finish first                         | **Migrate now** (none in progress/review)                 | Inventory + all defaults |
| 6   | Fold unstarted story files into entries and archive them?                                | Yes                                  | **Yes** (none today; 2.5–2.7 / 3.x / 4.x stay entry-only) | User: all defaults       |

Extra: unmatched done specs → epic-2 entries **8–10** with plans — **Yes** (recommended; all defaults).

Workspace / separate store repo: skipped (answers keep the store in this project).

## Checklist results

_(filled after execute)_

## Approval

**Approved 2026-10-03. Executed on branch chore/bmad-v7-migrate-artifacts. Backup: git history (no `_bmad-output-bak`).**
