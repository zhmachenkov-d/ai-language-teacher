---
title: "2.1 Outlook week-grid schedule UI"
type: "feature"
created: "2026-09-29"
status: "done"
route: "dispatch"
review_loop_iteration: 0
baseline_commit: "846674a92e72012b42d287a771411b1448cd7e31"
context:
  - "{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Onboarding schedule still uses a compact weekday+time list, so the epic Outlook week-grid AC and the reusable UI needed for Settings «изменить» (2.7) remain unmet.

**Approach:** Replace the schedule-step list with an Outlook-like Mon–Sun hour grid (hour-tall rows, scrollable full day) where weekly slots can start on `:00` or `:30`. Marks are **start-point chips** (not duration-tall blocks): `:00` at the top of the hour row, `:30` at mid-row. Same `{weekday, start_minute}` + timezone model; extract the grid for 2.7 mini-wizard reuse (not inline on Settings).

**Decisions:**

- SLOT_MODEL: unchanged shape — ISO weekday `0=Mon…6=Sun`, `start_minute` 0–1439 local; ≥1 slot; PATCH coalesce by `(weekday, start_minute)`
- GRID_ROWS: hour-tall rows for hours `0…23` (FULL_SCROLL); visual grain is 1 hour, not a separate :30 row
- HALF_SUPPORT: slots may use `start_minute = hour*60` (`:00`) or `hour*60+30` (`:30`); both are first-class
- CLICK_SPLIT: click upper half of an hour cell → toggle `:00`; lower half → toggle `:30`; halves independent
- MARK_POS: `:00` chip at top of hour cell; `:30` chip at vertical middle; chips do **not** stretch by `lesson_duration_minutes` (duration height is calendar/2.6). Only start-alignment (`:00` top / `:30` mid) is noted for later lesson blocks — not owned here
- FINE_SNAP: owned by `ScheduleWeekGrid` on bind — `start_minute` not on `:00`/`:30` snaps to nearest half-hour; on a tie (exact `:15`/`:45`), pick the **earlier** half; then coalesce; emit `snapped` for parent RU notice «время округлено до получаса»; never destroy a legitimate `:30`
- INITIAL_VIEW: working band = hours 7–20 visible (same labels as calendar `HOUR_START`…`HOUR_END` exclusive end); on first paint scroll so that band is in view; if any selected mark’s hour is outside 7–20, scroll so that hour row (incl. mid-chip for `:30`) is visible
- SURFACE: reusable `ScheduleWeekGrid`; do not fork CalendarHome
- SHARE: may import `WEEKDAY_LABELS_RU` from `calendarDates` only; no CalendarHome / `HOUR_*` edits
- PERSIST: existing `PATCH /learner` on «Далее»; no new API
- SETTINGS: COMPONENT_ONLY — Settings «Изменить» stays disabled; 2.7 mounts this grid later
- CELL_A11Y: each half is a real `button` with accessible name including weekday + `HH:MM`; Enter/Space toggles

## Boundaries & Constraints

**Always:**

- Russian chrome; one wizard screen = one step; coral «Далее»; GATE/RESUME/HANDOFF from 2.1 unchanged
- Wire `snake_case`; Bearer loopback only; errors `{code,message,retryable}`
- Timezone auto-detect + read-only confirmation on schedule step (AD-13)
- Grid mountable later from a Settings mini-wizard (props/events for slots)
- FULL_SCROLL hours `0…23`; `:00` and `:30` via CLICK_SPLIT; marks are start chips only
- FINE_SNAP in the grid before marks render; never leave a non-`:00`/`:30` slot selected-but-invisible

**Never:**

- Hour-only slots that forbid or auto-destroy `:30`
- Duration-tall slot marks sized by `lesson_duration_minutes`
- Settings Schedule/Goals persist, duration save, lesson reschedule, or enabling «Изменить» (2.7)
- Inline Outlook grid on the Settings page (UX-DR17)
- Compact draft list as the primary editor
- Clipping selectable hours to calendar 7–21
- Implementing CalendarHome lesson-event layout/height in this story
- Teacher domain/API/SQLite schema changes; slot model fork
- Surname/postal/email/phone; IPC as domain bus; Host/tray changes

## I/O & Edge-Case Matrix

| Scenario          | Input / State                      | Expected Output / Behavior                                | Error Handling                |
| ----------------- | ---------------------------------- | --------------------------------------------------------- | ----------------------------- |
| Toggle :00        | Click / Activate upper-half button | Slot `(weekday, hour*60)`; chip top of cell               | N/A                           |
| Toggle :30        | Click / Activate lower-half button | Slot `(weekday, hour*60+30)`; chip mid-cell               | N/A                           |
| Both halves       | :00 and :30 same weekday/hour      | Two independent slots/chips; both buttons selected        | N/A                           |
| Toggle remove     | Activate selected half button      | That half’s slot removed                                  | N/A                           |
| Zero slots        | No selections + «Далее»            | Advance blocked; clear RU copy                            | Stay                          |
| Hydrate :30       | Prior `start_minute=570`           | Stays 570; mid-chip; no snap notice                       | N/A                           |
| Hydrate evening   | Prior 22:30 only                   | Mid-chip hour 22; INITIAL_VIEW scrolls that row into view | N/A                           |
| Initial in-band   | Empty or only slots in hours 7–20  | Viewport shows working band 7–20                          | N/A                           |
| Fine :15          | Prior 09:15 (`555`)                | → `540` (09:00); notice; coalesce if 09:00 existed        | N/A                           |
| Fine :45          | Prior 09:45 (`585`)                | → `570` (09:30) earlier-on-tie; notice                    | N/A                           |
| Fine coalesce     | Prior 09:10 and 09:00              | Snap 09:10→09:00; one slot after coalesce                 | N/A                           |
| Persist OK        | ≥1 slot + timezone + «Далее»       | PATCH; next onboarding step                               | Error + retry if teacher down |
| Mid-wizard reopen | Partial saves                      | RESUME marks (+ fine snap if needed)                      | N/A                           |

</frozen-after-approval>

## Code Map

- `deferred-work.md` — on Done: `resolved_by` this spec **partial** — onboarding grid + extract; Settings mini-wizard mount remains 2.7 (do not claim calendar lesson layout done)
- `epic-2-context.md` / `epics.md` Story 2.1 schedule AC + Story 2.7 reuse
- `apps/desktop/src/renderer/src/views/OnboardingWizard.vue` — replace list with grid; fine-snap notice; PATCH/GATE/timezone
- `apps/desktop/src/renderer/src/onboarding/constants.ts` — `formatStartMinute` / helpers
- New `apps/desktop/src/renderer/src/components/ScheduleWeekGrid.vue` (+ Vitest) — 0–23 scroll; CLICK_SPLIT; MARK_POS chips; FINE_SNAP; named half-buttons; props/emit `WeeklySlot[]`
- `apps/desktop/src/renderer/src/calendar/calendarDates.ts` — read-only; optional import `WEEKDAY_LABELS_RU` only; no `HOUR_*` / CalendarHome edits
- `apps/desktop/src/renderer/src/views/CalendarHome.vue` — read-only density reference; do not edit
- `apps/desktop/src/renderer/src/services/teacherClient.ts` — `WeeklySlot` unchanged
- `apps/desktop/src/renderer/src/views/OnboardingWizard.spec.ts` — :00/:30, fine snap cases, INITIAL_VIEW, a11y buttons, zero-slot, PATCH
- `apps/desktop/src/renderer/src/views/SettingsView.vue` — «Изменить» stays disabled
- Do not change `services/teacher/` domain/API, Electron main/preload, or CalendarHome

## Tasks & Acceptance

**Execution:**

- [x] New `ScheduleWeekGrid.vue` (+ Vitest) — 0–23 scroll; INITIAL_VIEW; CLICK_SPLIT; start chips; FINE_SNAP emit; named half `button`s
- [x] `OnboardingWizard.vue` — mount grid; remove draft list; RU fine-snap notice; timezone + «Далее» PATCH
- [x] `OnboardingWizard.spec.ts` (+ grid spec) — matrix cases below; PATCH body slots+timezone
- [x] Leave Settings «Изменить» disabled; `npm test` + `npm run build`; deferred-work **partial** `resolved_by`

**Acceptance Criteria:**

- Given the schedule step, when the Learner activates the upper/lower half control of an hour cell, then a `:00` / `:30` slot toggles and a start chip sits top / mid-cell (not duration-tall)
- Given both halves of the same hour, when selected, then two slots exist, both named buttons stay independently focusable, and both chips render
- Given zero selected slots, when «Далее», then advance is blocked with clear Russian copy
- Given a prior `:30` slot, when the schedule step opens, then it remains `:30` (mid-chip) with no snap notice
- Given prior `09:15`, when the schedule step opens, then the grid emits `540` and the parent shows the RU notice; given `09:45`, then `570`; given `09:10`+`09:00`, then one coalesced `540`
- Given only in-band slots (or empty), when the schedule step opens, then the viewport shows hours 7–20; given only `22:30`, when it opens, then hour 22 (mid-chip) is scrolled into view
- Given ≥1 slot + timezone, when «Далее», then `PATCH /learner` persists slots and intake advances as today
- Given the grid alone, when driven by props/events, then it owns fine-snap, supports `:30`, scrolls 0–23, and does not depend on CalendarHome or Settings

## Implementation Notes

## Spec Change Log

## Review Triage Log

- blind: new component paths look mis-rooted in the diff vs apps/desktop — **false** — untracked `git diff --no-index` path artifact; files live under `apps/desktop/src/renderer/src/components/`
- blind: deferred `resolved_by` cites a spec absent from the staged diff — **false** — untracked `spec-2-1-outlook-week-grid-schedule.md` exists on disk; packaging of the review bundle, not a product defect
- blind: notice capitalization «Время» vs Intent quote «время» — **false** — Russian sentence case; same phrase
- blind: max-height 420px cannot show all hours 7–20 at once — **false** — Intent INITIAL_VIEW means scroll so the working band starts in view (hour 7), not that 14 rows fit simultaneously
- blind: fine-snap tests never click «Далее» to assert PATCH snapped slots — **medium** — confirmed; Persist OK + fine rows lack that assert. Route: patch
- blind: CELL_A11Y Enter/Space untested — **false** — halves are native `<button>`; browser keyboard activation; Intent does not require a keyboard harness
- blind: day headers `role=row` without `role=grid` — **low** — rejected (cosmetic; everyday use unaffected; Intent only requires named half buttons)
- blind: Settings «Изменить» disabled unchecked — **false** — COMPONENT_ONLY leaves Settings untouched; stub remains `disabled` in SettingsView.vue
- blind: CalendarHome independence test only mounts — **low** — rejected (weak test, no everyday harm; grid does not import CalendarHome)
- blind: `applyInitialScroll` only onMounted — **medium** — open after fine-snap can scroll pre-snap hour; no re-scroll when slots settle. Route: patch (group with edge first-paint/scroll)
- blind: invalid weekday not clamped — **medium** — confirmed; orphan slot with no half button. Route: patch (drop invalid weekday in normalize)
- blind: epic-2-context.md churn in the same diff — **false** — unrelated compile noise; not a schedule-grid defect
- blind: wizard scroll asserts hard-code `7*52` / `22*52` — **low** — rejected (test style; drift unlikely to hurt users)
- blind: no off-grid selection summary after list removal — **false** — Intent forbids compact list as primary editor; FULL_SCROLL + chips are the surface
- edge: `snapStartMinute` NaN/non-finite — **low** — rejected (API/UI never feed NaN; unlikely everyday)
- edge: weekday outside 0–6 persists — **medium** — same root as blind invalid weekday. Route: patch
- edge: skipWatch drops parent updates mid-tick — **maybe-false** — would need a concurrent parent write during the nextTick window; no demonstrated path in wizard. Rejected
- edge: first paint uses raw props → fine slot selected-but-invisible until parent round-trip — **high** — `selectedKeys`/`isSelected` read `props.slots`; no half for e.g. 555. Route: patch (group with claim FINE_SNAP-before-marks)
- edge: fine snap into out-of-band hour without post-snap scroll — **medium** — same INITIAL_VIEW/scroll root. Route: patch
- edge: multiple out-of-band marks only scroll earliest — **false** — Intent INITIAL_VIEW explicitly picks earliest outside mark
- edge: deletion of list orphans out-of-range weekdays — **medium** — same weekday clamp root. Route: patch
- edge claim: FINE_SNAP before marks render — **high** — carried with first-paint invisibility. Route: patch
- edge claim: INITIAL_VIEW uses post-snap hour — **medium** — carried with scroll-after-normalize. Route: patch
- verification-gap: nearer-upper `snapStartMinute` branch untested — **medium** — pre-verified; always-lower would still green. Route: patch
- verification-gap: INITIAL_VIEW pre-band hour &lt; 7 untested — **medium** — pre-verified; dropping `h < 7` would still green evening cases. Route: patch

## Design Notes

- Marks are start-point chips only. Calendar lesson **block height** from duration is 2.6; if 2.6 reuses start-alignment (`:00` top / `:30` mid of the hour row), that is alignment-only — do not treat this story as shipping lesson layout.
- Prefer coral-soft / surface selected chips — not lesson-event states (next/missed/done).
- FULL_SCROLL remains; EXPAND_BAND and hour-only NON_HOUR_SNAP are superseded.
- FINE_SNAP earlier-on-tie: `09:15→09:00`, `09:45→09:30`.

## Verification

**Commands:**

- `cd apps/desktop && npm test && npm run build` — Vitest + build green (grid + wizard schedule)

**Manual checks:**

- Wizard schedule: top/bottom of hour for :00/:30; evening via scroll; zero slots blocks; reopen keeps :30; finish → consent
