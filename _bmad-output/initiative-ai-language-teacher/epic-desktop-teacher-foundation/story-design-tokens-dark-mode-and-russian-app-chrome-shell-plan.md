---
title: "1.4 Design tokens and dark mode"
type: "feature"
ticket: 4
status: "done"
created: "2026-09-27"
baseline_revision: "7497f1e8dc03d51c94098ae9f3cf082b8b392ad9"
review_loop_iteration: 0
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Vue renderer still uses ad-hoc hex colors with light-only styling, so later screens have no shared token language.

**Approach:** Implement `neutral-cool-lines` light/dark CSS variables and OS+manual theme switching on the existing renderer surface. Russian nav shell / routed placeholders are deferred (`deferred-work.md`).

**Decisions:**

- Theme preference is three-way: `system` | `light` | `dark`. Persist in renderer `localStorage` under key `theme-preference` (UI chrome only — not Config/SQLite).
- Manual override control lives on the tokenized surface (not deferred to Settings 1.6).
- CSS custom properties are locked: `--color-bg`, `--color-surface`, `--color-sidebar`, `--color-ink`, `--color-muted`, `--color-line`, `--color-coral`, `--color-coral-cta`, `--color-coral-soft`, `--color-missed`, `--color-done`, `--color-on-coral`, `--color-today-tint`, plus `--font-sans` and `--radius-md` (4px). Apply effective theme via `document.documentElement.dataset.theme = 'light'|'dark'`.
- Dark `--color-today-tint` maps to DESIGN coral-soft-dark (`#352622`); light uses `#FFF9F7`.
- Do not edit `apps/desktop/src/renderer/index.html` in this slice (keep CSP/`lang` as-is; `color-scheme` comes from theme attr + CSS).
- Russian shell (Календарь / План / Прогресс / Настройки + vue-router) and nav/panel case rules (sentence case / ALL CAPS labels) stay deferred with that shell — this Done does not satisfy those epic ACs.

## Boundaries & Constraints

**Always:**

- CSS variables for the locked `--color-*` names above (light + dark pairs) — hex from DESIGN.md `neutral-cool-lines`
- Cool grey chrome; spark coral (`#FF8161`) never as body-text fill; filled CTAs use coral-cta + on-coral
- `--font-sans`: `"Segoe UI", "Helvetica Neue", Arial, sans-serif`; `--radius-md`: 4px; do not use `rounded.full` on this surface
- Theme follows OS `prefers-color-scheme` when preference is `system`; switches live on OS change and on manual override
- Replace hardcoded placeholder colors with token variables; keep a visible demo of surface/ink/muted/line + coral-cta sample (prove tokens work)
- Honor `prefers-reduced-motion` for any theme/UI transition used here

**Never:**

- Edit `index.html`; add `vue-router`; Russian nav shell or Calendar/Plan/Progress/Settings routes (deferred; Stories 1.5/1.6 consume the later shell)
- Calendar grid, Settings sections, teacher HTTP, Electron main/preload changes
- Tailwind / new CSS framework; committed secrets; vendor `_bmad/` edits
- Body text on spark coral; full-app warm wash; multi-shadow SaaS elevation
- Invent alternate token names beyond the locked `--color-*` / `--font-sans` / `--radius-md` set

## I/O & Edge-Case Matrix

| Scenario          | Input / State                         | Expected Output / Behavior                              | Error Handling                          |
| ----------------- | ------------------------------------- | ------------------------------------------------------- | --------------------------------------- |
| Fresh install     | No `theme-preference` in localStorage | Effective theme = OS; preference = `system`             | N/A                                     |
| Manual light/dark | User selects light or dark            | Tokens switch immediately; `theme-preference` persisted | Corrupt/unknown stored value → `system` |
| OS theme change   | Preference `system`; OS flips         | Live retoken without reload                             | N/A                                     |
| Reduce motion     | OS `prefers-reduced-motion: reduce`   | Theme/UI transitions effectively none                   | N/A                                     |

</frozen-after-approval>

## Code Map

- `_bmad-output/initiative-ai-language-teacher/epic-1-context.md` — token/chrome constraints; shell later
- `_bmad-output/planning-artifacts/epics.md` (Story 1.4) — AC source; Russian shell AC deferred
- `_bmad-output/initiative-ai-language-teacher/ux-ai-language-teacher/DESIGN.md` — locked hex pairs, type, radius
- `_bmad-output/initiative-ai-language-teacher/deferred-work.md` — Russian shell split entry
- `apps/desktop/src/renderer/src/App.vue` — replace ad-hoc hex with tokenized demo + theme control
- `apps/desktop/src/renderer/src/main.ts` — import tokens CSS
- `apps/desktop/src/renderer/src/styles/tokens.css` (new) — light/dark `--color-*` pairs + `--font-sans` / `--radius-md` + reduce-motion helpers
- `apps/desktop/src/renderer/src/composables/useTheme.ts` (new) — preference via `theme-preference`, OS listener, apply `dataset.theme`
- Do not change: `apps/desktop/src/renderer/index.html`, `apps/desktop/src/main/**`, `apps/desktop/src/preload/**`, `services/teacher/**`, no `vue-router` pin

## Tasks & Acceptance

**Execution:**

- [x] `apps/desktop/src/renderer/src/styles/tokens.css` -- Locked `--color-*` / `--font-sans` / `--radius-md` light+dark + reduce-motion -- UX-DR1/2/3
- [x] `apps/desktop/src/renderer/src/composables/useTheme.ts` -- system/light/dark via `theme-preference`, OS listen, apply `dataset.theme` -- UX-DR1
- [x] `apps/desktop/src/renderer/src/App.vue` + `main.ts` -- Tokenized surface + theme control; drop hardcoded hex -- UX-DR4
- [x] Verify typecheck + build; spot-check theme matrix + reduce-motion -- I/O matrix

**Acceptance Criteria:**

- Given the Vue renderer, when tokens render, then cool-grey surfaces use the locked DESIGN `--color-*` set and spark coral is not used as body text fill
- Given OS theme and in-app `system|light|dark` control, when preference or OS theme changes, then light/dark token sets apply without reload and preference is stored under `theme-preference`
- Given typography/shape tokens, when the tokenized surface renders, then `--font-sans` and `--radius-md` (4px) apply; `rounded.full` unused
- Given this slice reaches Done, when sprint status is updated, then Russian nav shell / UX-DR20 routed chrome (and nav/panel case rules) remain open via deferred-work — not satisfied by this Done

### Review Findings

- [x] [Review][Patch] Reduce-motion test bypasses media query gate [`apps/desktop/src/renderer/src/composables/useTheme.spec.ts:197`]
- [x] [Review][Patch] App theme click does not assert preference binding [`apps/desktop/src/renderer/src/App.spec.ts:47`]
- [x] [Review][Patch] Corrupt theme-preference fallback does not assert preference === system [`apps/desktop/src/renderer/src/composables/useTheme.spec.ts:116`]
- [x] [Review][Patch] Product tsconfig.web.json typechecks renderer `*.spec.ts` without exclude [`apps/desktop/tsconfig.web.json:18`]
- [x] [Review][Defer] Epic Story 1.4 in epics.md still presents Russian chrome / UX-DR20 ACs without deferral cross-reference [`_bmad-output/planning-artifacts/epics.md:230`] — deferred: same class as 1.3 epics drift; deferred-work already records the shell split
- [x] [Review][Defer] AGENTS.md desktop verify path omits `npm test` / Vitest after first renderer harness [`AGENTS.md`] — deferred: fix edits agent-context AGENTS.md

**Rejected**

- false — Blind: swatches omit ink/muted as chips — disproved: `.ink`/`.muted` text + line swatch + Sample CTA prove the locked demo set
- false — Blind: corrupt storage leaves bad key — matrix only requires effective `system`; prior triage already allowed leaving the key
- false — Blind: Spec `status: done` vs sprint `review` — sprint correctly tracks review; frontmatter Done means implementation tasks complete
- low — Blind: Spec Change Log empty / review_loop_iteration 0 / English labels not in Intent / stale “5 tests” count — fix would edit the spec under review
- low — Blind: sprint key still names russian-app-chrome-shell — renaming keys costs more than everyday confusion; deferred-work is authoritative
- low — Blind: radiogroup missing arrow-key roving — Tab still reaches each button; full radiogroup keyboard is complexity beyond everyday personal-desktop theme toggle
- low — Blind: global `*` reduce-motion `!important` — common pattern; scoped opt-out would add complexity without a demonstrated break
- low — Blind: localStorage throw/quota missing from matrix — code already catches; matrix row would be a spec edit
- low — Edge: matchMedia missing/throws; OS flip before onMounted; preference Ref assign without setPreference; no cross-window `storage` listener — unlikely everyday on Electron single-window; prior triage rejected the same class

## Implementation Notes

- Added `tokens.css` with locked DESIGN hex pairs; dark `--color-today-tint` = `#352622`.
- `useTheme` + `bootstrapTheme`: `theme-preference` localStorage; corrupt → `system`; OS `matchMedia` listener; `dataset.theme`.
- `App.vue` tokenized demo + System/Light/Dark control; coral only on sample CTA via `--color-coral-cta` / `--color-on-coral`.
- Matrix covered by vitest (`useTheme.spec.ts` + `App.spec.ts`): fresh/OS, manual persist, corrupt→`system` preference, OS live/ignored, return-to-system, reduce-motion CSSOM gate + main import, App click binding. `npm test` → 9 passed; typecheck + build clean.
- Russian shell remains deferred.

## Spec Change Log

## Review Triage Log

- false — Blind: new-file hunks omit `apps/desktop/` prefix — disproved: files live under `apps/desktop/`; `git diff --no-index` path presentation artifact
- medium — Blind: package-lock still records caret ranges while package.json pins exact versions — verified package-lock.json lines for @vue/test-utils/happy-dom/vitest — route patch
- low — Blind: matrix tests miss bootstrap-from-stored light/dark, return-to-system, OS-ignored-when-manual — partially real; OS-ignored covered by VG; remaining cases absorbed into patch tests
- false — Blind: corrupt theme-preference never cleared from localStorage — matrix only requires effective `system`; leaving bad key is allowed
- false — Blind: English System/Light/Dark labels vs UX-DR20 Russian — narrowed Intent defers Russian chrome; theme demo labels not required Russian
- false — Blind: swatches omit coral/missed/done — frozen demo requires surface/ink/muted/line + coral-cta sample only
- low — Blind: theme buttons/CTA lack `:focus-visible` — verified App.vue styles; keyboard focus weak — route patch
- low — Blind: aria-pressed group vs radiogroup — verified App.vue; under-describes single-select — route patch
- low — Blind/Edge: no `storage` listener for cross-window preference — real in theory; v1 single-window desktop unlikely everyday; reject (complexity > everyday harm)
- low — Blind: deprecated transitive glob@10 via @vue/test-utils — npm notice only; no demonstrated break; reject
- false — Blind: sprint-status/deferred-work absent from diff — disproved: both appear in tracked hunks; Done sync is present-step
- low — Edge: matchMedia missing/throws — Electron renderer always provides matchMedia; unlikely everyday; reject
- low — Edge: OS flip between setup and onMounted — millisecond race after bootstrapTheme; unlikely everyday; reject
- medium — VG: manual light/dark does not assert OS changes are ignored — carried as filed — route patch
- medium — VG: reduce-motion check is source-text only — carried as filed — route patch
- medium — VG: App theme-control click path untested — carried as filed — route patch

## Design Notes

Effective theme: `dataset.theme = 'light'|'dark'` from preference + `matchMedia('(prefers-color-scheme: dark)')`. Demo may show sample CTA using `--color-coral-cta` + `--color-on-coral` only.

## Verification

**Commands:**

- `cd apps/desktop && npm install && npm test && npm run typecheck && npm run build` -- expected: 9 theme/chrome tests green; clean typecheck + production build

**Manual checks:**

- Toggle system/light/dark; flip OS theme while on `system` — tokens update live
- Enable OS reduce-motion — theme change has no noticeable animation
