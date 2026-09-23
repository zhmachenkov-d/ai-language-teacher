---
name: ai-language-teacher
description: Electron desktop AI language teacher — calendar-first working tool with coral spark accents.
status: final
updated: 2026-09-23
sources:
  - {planning_artifacts}/prds/prd-ai-language-teacher-2026-09-22/prd.md
  - {planning_artifacts}/prds/prd-ai-language-teacher-2026-09-22/addendum.md
colors:
  # neutral-cool-lines (locked). Light = default; *-dark = dark mode (OS follow + manual override).
  bg: '#F7F8F9'
  surface: '#FFFFFF'
  sidebar: '#F3F4F6'
  ink: '#1A1C1E'
  muted: '#6B7280'
  line: '#D1D5DB'
  coral: '#FF8161'
  coral-cta: '#B75C45'
  coral-soft: '#FFE8E2'
  missed: '#C44B3A'
  done: '#5A5A5A'
  on-coral: '#FFFFFF'
  today-tint: '#FFF9F7'
  bg-dark: '#16181A'
  surface-dark: '#1E2124'
  sidebar-dark: '#1A1D20'
  ink-dark: '#E8EAED'
  muted-dark: '#9AA0A8'
  line-dark: '#343A40'
  coral-dark: '#FF8161'
  coral-cta-dark: '#B75C45'
  coral-soft-dark: '#352622'
  missed-dark: '#E07060'
  done-dark: '#8E949A'
  on-coral-dark: '#FFFFFF'
typography:
  body:
    fontFamily: '"Segoe UI", "Helvetica Neue", Arial, sans-serif'
  nav:
    fontFamily: '"Segoe UI", "Helvetica Neue", Arial, sans-serif'
  label-caps:
    fontFamily: '"Segoe UI", "Helvetica Neue", Arial, sans-serif'
rounded:
  md: 4px
  full: 9999px
spacing:
  # Numeric unit scale not locked — density qualitative. Owner: custom dense tool chrome (not a named UI kit).
  density: outlook-dense
components:
  calendar-event-block:
    next-emphasis: bold + background '{colors.coral-soft}' + coral spark mark
    missed-mark: '{colors.missed}' + exclamation icon
    done: '{colors.done}'
    radius: '{rounded.md}'
  week-month-switcher:
    surface: '{colors.surface}'
    ink: '{colors.ink}'
    line: '{colors.line}'
    radius: '{rounded.md}'
  side-panel:
    surface: '{colors.surface}'
    label: '{typography.label-caps}'
  cta-button-coral:
    background: '{colors.coral-cta}'
    foreground: '{colors.on-coral}'
    radius: '{rounded.md}'
  numbered-plan-steps:
    background: '{colors.coral-cta}'
    foreground: '{colors.on-coral}'
    radius: '{rounded.full}'
  accent-rule:
    color: '{colors.coral}'
  chat-bubble:
    teacher-fill: '{colors.sidebar}'
    learner-fill: '{colors.coral-soft}'
    radius: '{rounded.md}'
    ink: '{colors.ink}'
  inline-pronunciation-feedback:
    ink: '{colors.ink}'
    muted: '{colors.muted}'
    accent: '{colors.coral}'
  mic-control:
    shape: round
    radius: '{rounded.full}'
    resting-border: '{colors.line}'
    resting-ink: '{colors.muted}'
    active-fill: '{colors.coral}'
    active-ink: '{colors.on-coral}'
  listening-card:
    surface: '{colors.surface}'
    border: '{colors.line}'
    radius: '{rounded.md}'
    option-selected-fill: '{colors.coral-soft}'
    option-selected-border: '{colors.coral}'
    player-chrome: neutral '{colors.ink}' / '{colors.muted}' / '{colors.line}'
  history-bottom-bar:
    surface: '{colors.surface}'
    border-top: '{colors.line}'
    label: '{typography.label-caps}'
  onboarding-step:
    surface: '{colors.surface}'
    bg: '{colors.bg}'
    radius: '{rounded.md}'
  living-plan-document:
    surface: '{colors.surface}'
    bg: '{colors.bg}'
    accent-rule: '{colors.coral}'
  progress-sections:
    surface: '{colors.surface}'
    bg: '{colors.bg}'
    accent: '{colors.coral}'
  settings-sections:
    surface: '{colors.surface}'
    bg: '{colors.bg}'
  telegram-result-card:
    # Companion surface; reuse coral-cta for emphasis sparingly; inherit ink/muted hierarchy.
    accent: '{colors.coral-cta}'
    ink: '{colors.ink}'
---

## Brand & Style

This product is a **working tool** (рабочий инструмент), not entertainment or a game-first experience. UI voice is **friendly** (дружеский) — supportive coach, not formal/strict-teacher. Anti-patterns: sterile SaaS chrome and kids language-app UI.

Visual direction is the locked hybrid of **coral-accent-tool** (Outlook-like density, cool chrome, coral as spark only) plus **numbered-coach** motifs (numbered circles and short accent rules in plan / side panel). Forks locked: sentence case in app nav; ALL CAPS only for panel/section labels; light sidebar (not charcoal nav). Primary light surfaces are cool grey from **neutral-cool-lines** — not a full warm wash.

From the Language Center flyer PSD (`imports/template.psd`), lift only: **A** palette (coral + white/grey/charcoal), **B** clean sans typography, **C** numbered coral circles + accent rules, **E** warm adult-education mood. Do **not** lift stock people/flags photography.

**Visual references** (illustrative; spines win on conflict):

- Wireframes: `wireframes/flow-calendar-home-2026-09-22.excalidraw`, `wireframes/flow-lesson-screen-2026-09-22.excalidraw`
- Key mocks: `mockups/key-calendar-home.html`, `mockups/key-lesson.html`, `mockups/key-connectivity-modal.html`, `mockups/key-lesson-history.html`, `mockups/key-progress.html`
- Direction hybrid sources: `mockups/direction-coral-accent-tool.html`, `mockups/direction-numbered-coach.html`
- Color themes board: `mockups/color-themes-hybrid-1-3.html` (locked pick: **neutral-cool-lines**)
- Brand import: `imports/template.psd` (lift A/B/C/E only — see `.working/reconcile-template-psd.md`)

## Colors

Theme: **neutral-cool-lines** (light + dark). Dark mode follows OS theme with a manual override.

| Role          | Light                 | Dark                                          | Use                                                                                                     |
| ------------- | --------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Canvas        | `{colors.bg}`         | `{colors.bg-dark}`                            | App background                                                                                          |
| Surface       | `{colors.surface}`    | `{colors.surface-dark}`                       | Panels, cards, calendar sheet                                                                           |
| Sidebar       | `{colors.sidebar}`    | `{colors.sidebar-dark}`                       | Light nav / plan chrome                                                                                 |
| Ink           | `{colors.ink}`        | `{colors.ink-dark}`                           | Primary text                                                                                            |
| Muted         | `{colors.muted}`      | `{colors.muted-dark}`                         | Secondary text, meta                                                                                    |
| Line          | `{colors.line}`       | `{colors.line-dark}`                          | Dividers, grid rules                                                                                    |
| Coral (spark) | `{colors.coral}`      | `{colors.coral-dark}`                         | Non-text spark: next soft emphasis, today line/pill edge, missed `!`, accent rules, option borders      |
| Coral CTA     | `{colors.coral-cta}`  | `{colors.coral-cta-dark}`                     | Filled primary CTAs + numbered step circles with `{colors.on-coral}` text                               |
| Coral soft    | `{colors.coral-soft}` | `{colors.coral-soft-dark}`                    | Soft fill (next event, selected option, learner bubble)                                                 |
| Missed        | `{colors.missed}`     | `{colors.missed-dark}`                        | Missed lesson mark                                                                                      |
| Done          | `{colors.done}`       | `{colors.done-dark}`                          | Completed lesson mark                                                                                   |
| On coral      | `{colors.on-coral}`   | `{colors.on-coral-dark}`                      | Text/icon on `{colors.coral-cta}` fill                                                                  |
| Today tint    | `{colors.today-tint}` | use `{colors.coral-soft-dark}` wash sparingly | Faint warm wash on **calendar today cell only** (light); dark uses soft-dark wash, not a global surface |

**Spark vs CTA:** `{colors.coral}` `#FF8161` is spark-only (not body text on coral). Filled buttons and numbered circles use `{colors.coral-cta}` `#B75C45` so `{colors.on-coral}` meets contrast.

### Contrast targets (measured, WCAG AA intent)

| Pair                                               | Ratio | AA normal text (4.5:1)                         |
| -------------------------------------------------- | ----- | ---------------------------------------------- |
| `{colors.ink}` / `{colors.bg}`                     | 16.07 | Pass                                           |
| `{colors.muted}` / `{colors.surface}`              | 4.83  | Pass                                           |
| `{colors.missed}` / `{colors.surface}`             | 4.76  | Pass                                           |
| `{colors.on-coral}` / `{colors.coral-cta}`         | 4.54  | Pass                                           |
| `{colors.ink-dark}` / `{colors.bg-dark}`           | 14.77 | Pass                                           |
| `{colors.muted-dark}` / `{colors.surface-dark}`    | 6.14  | Pass                                           |
| `{colors.missed-dark}` / `{colors.surface-dark}`   | 5.13  | Pass                                           |
| `{colors.on-coral}` / `{colors.coral}` (`#FF8161`) | 2.45  | **Fail — do not put body text on spark coral** |

Incomplete («Не завершен») calendar-event fill/border: reuse `{colors.coral-soft}` border + `{colors.muted}` label; no new brand hue.

## Typography

Stack: **"Segoe UI", "Helvetica Neue", Arial, sans-serif**.

| Role                      | Case / use                                           |
| ------------------------- | ---------------------------------------------------- |
| `{typography.nav}` / body | Sentence case for app navigation and running UI copy |
| `{typography.label-caps}` | ALL CAPS for panel and section labels only           |

Font sizes, weights, line heights: inherit **Electron/Chromium platform-sensible defaults** for custom chrome (no named UI-kit inheritance). Lock a numeric ramp later if needed.

## Layout & Spacing

Content density is **Outlook-like dense**: timed week/month calendar home, dense dashboards (Progress, Settings, Living plan). Default calendar grain is week; month is available. Lesson preview lives in a **side panel beside the calendar** (not modal/sheet). Lesson screen: dialogue dominates center; plan stages in a left sidebar.

`{spacing.density}` is qualitative. Numeric spacing scale deferred to implementation as a dense tool scale — not editorial whitespace.

## Elevation & Depth

Keep elevation **minimal** — desktop tool, not floaty SaaS. Prefer tonal/surface and line separation over stacked shadows. Exact shadow values deferred; avoid decorative multi-layer elevation.

Motion: moderate transitions for panels/screens; respect OS reduce-motion.

## Shapes

| Token            | Value      | Use                                                        |
| ---------------- | ---------- | ---------------------------------------------------------- |
| `{rounded.md}`   | ~4px       | Chrome and controls (buttons, event blocks, cards, inputs) |
| `{rounded.full}` | full round | Numbered step circles + mic control                        |

## Components

Canonical names match `EXPERIENCE.md` Component Patterns. Visual tokens below are locked; behavior lives in EXPERIENCE.

### Calendar event block

Timed event on an Outlook-style hour grid.

- **Completed** — `{colors.done}`
- **Scheduled** (future, not next) — quiet mark; side panel without «Начать урок»
- **Next scheduled** — bold + `{colors.coral-soft}` background + coral spark mark
- **Missed** — `{colors.missed}` + exclamation
- **Incomplete («Не завершен»)** — `{colors.coral-soft}` border + `{colors.muted}` label (resumable)

Today separate: Outlook-like pill date; current-time line; light `{colors.today-tint}` on today cell.

### Week / month switcher

Calendar chrome: week default, month available, Today / prev / next. Surface/ink/line; `{rounded.md}` controls.

### Side panel

Beside the calendar. Empty hint: «выберите урок для просмотра краткой информации или истории». Labels `{typography.label-caps}`. Numbered steps + accent rules in plan preview.

### CTA button (coral)

Primary filled actions («Начать урок», «Продолжить», primary Settings saves where coral): `{colors.coral-cta}` + `{colors.on-coral}`, `{rounded.md}`. Secondary actions use ink/line chrome, not spark fill.

### Numbered plan steps

Stage list: `{colors.coral-cta}` circle, `{colors.on-coral}` numeral, `{rounded.full}`; short `{colors.coral}` accent rules at section headings.

### Accent rule

Short coral spark rule near panel/section headings (plan / side panel). Color `{colors.coral}`.

### Chat bubble

Teacher fill `{colors.sidebar}`; learner fill `{colors.coral-soft}`; `{rounded.md}`; `{colors.ink}` text. Pronunciation feedback sits under the learner bubble.

### Inline pronunciation feedback

Under learner bubble: issue + corrected model; `{colors.ink}` / `{colors.muted}` with optional `{colors.coral}` accent on the corrected fragment.

### Mic control

Always-visible round control (`{rounded.full}`). Resting: `{colors.line}` / `{colors.muted}`. Active/hold: `{colors.coral}` fill + `{colors.on-coral}` icon (hold feedback may use spark coral; prefer high-contrast icon).

### Listening card

`{colors.surface}` + `{colors.line}` border + `{rounded.md}`. A/B/C options; selected = `{colors.coral-soft}` fill + `{colors.coral}` border. Player chrome neutral (ink/muted/line). Transcript hidden until after answer.

### History bottom bar

Replaces live mic: summary + template decision; surface + top line; labels `{typography.label-caps}`.

### Onboarding step

Wizard surfaces on `{colors.bg}` with `{colors.surface}` sections; coral spark/CTA only for primary actions and motifs — inherited tokens, no new hues.

### Living plan document

Full-screen document on `{colors.bg}` with `{colors.surface}` sections; coral spark/CTA only for primary actions and motifs — inherited tokens, no new hues.

### Progress sections

Full-screen dashboard sections on `{colors.bg}` with `{colors.surface}` blocks; coral spark/CTA only for primary actions and motifs — inherited tokens, no new hues.

### Settings sections

Full-screen settings sections on `{colors.bg}` with `{colors.surface}` blocks; coral spark/CTA only for primary actions and motifs — inherited tokens, no new hues.

### Telegram result card

Companion Telegram UI: ink hierarchy + sparingly `{colors.coral-cta}` emphasis on score/errors.

## Do's and Don'ts

| Do                                                                                                  | Don't                                               |
| --------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Dense working tool with friendly copy                                                               | Kids language-app or game-first chrome              |
| Spark `{colors.coral}` for non-text accents; `{colors.coral-cta}` for filled CTA + numbered circles | Body text on `#FF8161`; large coral brochure blocks |
| Cool grey surfaces; today-tint only on today cell                                                   | Full-app warm wash as primary surface               |
| Sentence case nav; ALL CAPS panel/section labels only                                               | ALL CAPS navigation                                 |
| Light sidebar; Outlook-like timed calendar                                                          | Charcoal nav; sparse dots calendar                  |
| `{rounded.md}` chrome; full round for circles + mic                                                 | Soft oversized consumer pills on tool chrome        |
| Minimal elevation; moderate motion + reduce-motion                                                  | Floaty multi-shadow SaaS                            |
| Lift PSD A/B/C/E                                                                                    | Stock people/flags photography                      |
| Prefer spines over illustrative wireframes/directions                                               | Treat direction HTML pixels as locked tokens        |
