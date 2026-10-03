---
title: "1.5 Calendar home empty chrome with side panel"
type: "feature"
ticket: 5
status: "done"
created: "2026-09-28"
baseline_revision: "4fd77e5cdeb9bb3e27d9d7450aec4eb81bced1db"
review_loop_iteration: 0
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The renderer is still a token demo — Learners lack the Outlook-like Calendar home (with empty side panel) that UX treats as the primary working surface.

**Approach:** Ship the deferred Russian nav shell (Calendar default) and an empty Outlook-like Calendar home: timed week (default) and month, today orientation, empty hour grid, and a beside-calendar side panel with the locked empty hint; keep System/Light/Dark in shell chrome.

**Decisions:**

- SHELL: absorb deferred Russian nav + pin `vue-router` with `createWebHashHistory` (no `index.html` CSP edits); Calendar default; unknown hash redirects to Calendar; План / Прогресс / Настройки are title-only stubs (Settings body = Story 1.6)
- THEME_CONTROL: keep English System/Light/Dark radiogroup in shell chrome on every primary route (nav footer or top chrome — implementer picks one placement)
- TODAY_RULES: week → date pill + now-line when today column visible and local now is inside 07:00–21:00 (else hide/clamp now-line); month → date pill + today-tint only (no horizontal now-line)
- WEEK_START: Monday-first (`weekStart=1`) for week and month headers, independent of OS/`Intl` locale
- SIDE_PANEL: ~300px panel mounts only on Calendar; stub routes are full-screen without the calendar panel

## Boundaries & Constraints

**Always:**

- Russian nav: Календарь / План / Прогресс / Настройки (sentence case); pin exact `vue-router`; `createWebHashHistory`; Calendar is the default route after the shell mounts; catch-all → Calendar
- Stub routes: full-screen title-only placeholders («План» / «Прогресс» / «Настройки»); no section shells, no save, no calendar side panel
- Default grain is week; month available; toolbar: «Неделя» / «Месяц» + «Сегодня» / prev / next (UX-DR6)
- Timed week hour band 07:00–21:00; empty cells only — no fake/demo events; elevation is tonal/line only (no stacked SaaS shadows)
- Today: `--color-today-tint` only on the today cell; week/month rules per TODAY_RULES (UX-DR5 partial)
- Side panel only on Calendar (~300px, not modal); empty hint exactly «выберите урок для просмотра краткой информации или истории»
- Reuse `tokens.css` + `useTheme`; English theme control visible on all primary routes; cool grey chrome; coral as spark only (pill/now-line accents OK)
- Nav/body sentence case; panel labels may be ALL CAPS; `--radius-md` (4px); honor `prefers-reduced-motion` (no route/view/now-line animation)
- Monday-first week/month columns (`weekStart=1`); “today” / now-line use browser local time (learner TZ deferred)
- Renderer-only under `apps/desktop/src/renderer/`

**Never:**

- Real lesson events, selection→preview CTAs, first-lesson tip, Living plan / Progress body content
- Settings section body (Story 1.6) — title stub only; do not change teacher HTTP, Electron main, or preload
- Fake demo events; modal/sheet side panel; app-wide warm wash; `createWebHistory` / CSP/`index.html` edits for routing
- Edit `services/teacher/**`, `apps/desktop/src/main/**`, `apps/desktop/src/preload/**`, `apps/desktop/src/renderer/index.html`

## I/O & Edge-Case Matrix

| Scenario               | Input / State                            | Expected Output / Behavior                                             | Error Handling |
| ---------------------- | ---------------------------------------- | ---------------------------------------------------------------------- | -------------- |
| Default open           | App mounts with shell                    | Hash Calendar week + empty side-panel hint; theme control visible      | N/A            |
| Stub routes            | Nav to План / Прогресс / Настройки       | Full-screen title stub; no calendar panel; theme control still visible | N/A            |
| Unknown hash           | Unmatched route                          | Redirect to Calendar                                                   | N/A            |
| Grain switch           | «Месяц» / «Неделя»                       | Empty grid; today oriented per TODAY_RULES when visible                | N/A            |
| Navigate               | «Сегодня» / prev / next                  | Anchor moves; «Сегодня» snaps to current local week/month              | N/A            |
| Today week in-band     | Today column visible; now in 07:00–21:00 | Pill + now-line + today-tint on today cell only                        | N/A            |
| Today week out-of-band | Today visible; now outside 07:00–21:00   | Pill + tint; now-line hidden or clamped — not off-grid                 | N/A            |
| Today month            | Today cell in month sheet                | Pill + today-tint only; no now-line                                    | N/A            |
| Today off-range        | Navigated away from today                | No now-line; no today-tint cells                                       | N/A            |
| Monday-first           | OS locale Sunday-first                   | Week and month headers still Пн…Вс (`weekStart=1`)                     | N/A            |
| Empty selection        | No lesson selected on Calendar           | Exact empty hint copy in side panel                                    | N/A            |
| Reduce motion          | `prefers-reduced-motion: reduce`         | No noticeable route/view/now-line animation                            | N/A            |

</frozen-after-approval>

## Design Notes

Layout cue (mockup): left nav → main toolbar (range title + «Неделя» | «Месяц» + ‹ Сегодня ›) → calendar sheet → ~300px side panel. Now-line uses coral spark; today pill uses coral border + tint — not coral as the body-text background. Russian localized range titles preferred (mockup pattern); exact format implementer-owned.

## Code Map

- `_bmad-output/implementation-artifacts/epic-1-context.md` — calendar + chrome constraints
- `_bmad-output/planning-artifacts/epics.md` (Story 1.5) — AC source
- `_bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/EXPERIENCE.md` — empty side panel + today orientation
- `_bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/mockups/key-calendar-home.html` — layout cue
- `_bmad-output/implementation-artifacts/deferred-work.md` — Russian shell from 1.4 (absorbed; resolve on Done)
- `_bmad-output/implementation-artifacts/spec-1-4-design-tokens-dark-mode-and-russian-app-chrome-shell.md` — tokens/`useTheme` continuity
- `apps/desktop/package.json` — pin exact `vue-router`
- `apps/desktop/src/renderer/src/main.ts` — `createApp` + hash router
- `apps/desktop/src/renderer/src/App.vue` — shell (nav + theme control + `<RouterView>`); replace token-demo surface
- `apps/desktop/src/renderer/src/styles/tokens.css` — reuse; do not edit token values
- `apps/desktop/src/renderer/src/composables/useTheme.ts` — reuse preference/OS theme
- New under `apps/desktop/src/renderer/src/`: hash router, shell/nav, CalendarHome (week/month + toolbar + panel), title stubs for План/Прогресс/Настройки
- Tests: extend `App.spec.ts` / add calendar + router specs; reuse vitest + happy-dom from 1.4

## Tasks & Acceptance

**Execution:**

- [x] `apps/desktop/package.json` + hash router — pin `vue-router`; `createWebHashHistory`; Calendar default + catch-all; title stubs — closes 1.4 deferred shell
- [x] `apps/desktop/src/renderer/src/App.vue` (+ shell/nav) — Russian nav + English theme control on all primary routes + `<RouterView>` — UX-DR20 shell
- [x] Calendar home — week default + month, toolbar, 07:00–21:00 empty grid, today per TODAY_RULES, Monday-first — UX-DR5/6
- [x] Calendar-only side panel with locked empty hint; tonal/line elevation — UX-DR6
- [x] Unit-test I/O matrix rows; typecheck + build — I/O matrix
- [x] On Done: `sprint-status.yaml` 1-5 → done; annotate deferred Russian-shell entry `resolved_by: spec-1-5-…` in Implementation Notes (keep ledger row) — sprint sync

**Acceptance Criteria:**

- Given the Russian nav shell, when the app opens, then Calendar is the default hash route, План / Прогресс / Настройки are title-only stubs, unknown hashes redirect to Calendar, and the System/Light/Dark theme control remains in shell chrome on every primary route
- Given Calendar home, when the Learner views it, then timed week (07:00–21:00) is default, month is available, «Сегодня» / prev / next work, and week/month columns are Monday-first regardless of OS locale
- Given today is visible, when week renders with now in-band, then date pill + now-line + today-tint appear on the today cell only; when month renders, then pill + today-tint only (no now-line)
- Given no lesson selected on Calendar, when the side panel renders, then it shows «выберите урок для просмотра краткой информации или истории»; stub routes have no calendar panel
- Given no scheduled lessons, when the grid renders, then it is empty (no fake events) with tonal/line elevation only

## Verification

**Commands:**

- `cd apps/desktop && npm install && npm test && npm run typecheck && npm run build` — expected: calendar/shell tests green; clean typecheck + production build

**Manual checks:**

- Walk I/O matrix rows; confirm theme control on stubs and reduce-motion quiet

## Implementation Notes

- Pinned `vue-router@5.3.1`; hash router with Calendar default + catch-all; Russian nav shell absorbs 1.4 deferred chrome.
- Theme control (System/Light/Dark) lives in nav footer; visible on Calendar and stub routes.
- Calendar: Monday-first week/month; timed week 07:00–21:00 empty grid; today pill/tint/now-line per TODAY_RULES; ~300px side panel with locked empty hint.
- Deferred Russian-shell ledger row kept; annotated `resolved_by: spec-1-5-calendar-home-empty-chrome-with-side-panel.md`.
- Verified: `npm test` (31), `npm run typecheck`, `npm run build`.
- Review patches: now-line top %, hour-label DOM, cross-month title, month toolbar nav, theme aria-checked, reduce-motion CSS gate, lazy router factory, goToday refreshes now, focus-visible + aria-current, month header order assert, named catch-all, localDayKey.

## Spec Change Log

## Review Triage Log

- false — Blind: new-file hunks omit `apps/desktop/` prefix — disproved: files live under `apps/desktop/src/renderer/`; `git diff --no-index` path presentation artifact when cwd was `apps/desktop`
- false — Blind: Done checklist (sprint-status / deferred `resolved_by`) absent from change set — disproved: both appear in tracked hunks vs baseline
- false — Blind: empty side panel lacks durable structure — disproved: `<aside class="panel" aria-label="Панель урока">` + locked empty hint; populated ALL-CAPS kickers are out of empty-chrome scope
- false — Blind: vue-router@5.3.1 lockfile reclassifies toolchain toward production — no demonstrated break; pin matches Vue 3.5.43 peer; reject
- low — Blind: incomplete ARIA grid/table around week `columnheader` — unlikely everyday harm on personal-desktop empty chrome; full grid pattern would add complexity without a demonstrated AT break; reject
- medium — VG: now-line CSS `top` percent never asserted at CalendarHome boundary — route patch
- medium — VG: timed week hour labels only unit-tested, not in mounted DOM — route patch
- medium — VG/Blind: cross-month `formatWeekRangeTitle` untested — route patch
- medium — VG/Blind: month-grain «Сегодня»/prev/next untested at UI — route patch
- medium — VG: theme `aria-checked` / active binding lost after ThemeControl extract — route patch
- medium — VG/Blind: App.spec reduce-motion case does not observe animation behavior — route patch
- medium — Edge: eager `export const router = createAppRouter()` duplicates hash listeners under App.spec — route patch
- medium — Edge: `goToday` uses stale `now` across 30s tick / midnight gap — route patch
- low — Blind: nav/toolbar lack `:focus-visible` unlike ThemeControl — route patch
- low — Blind: active nav missing `aria-current="page"` — route patch
- low — Blind: month Monday-first assertion weaker than week — route patch
- low — Blind: catch-all redirects to string `'/calendar'` vs named route — route patch
- low — Blind: Vue keys use `day.toISOString()` on local midnight Dates — route patch
- low — VG: production `main.ts` `.use(router)` never executed by tests — defer (App.spec supplies its own router; entry wiring smoke is low leverage for this chrome story)
