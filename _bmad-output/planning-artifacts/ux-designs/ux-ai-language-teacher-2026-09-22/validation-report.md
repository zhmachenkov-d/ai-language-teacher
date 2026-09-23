# Validation Report — ai-language-teacher

- **DESIGN.md:** `_bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/DESIGN.md`
- **EXPERIENCE.md:** `_bmad-output/planning-artifacts/ux-designs/ux-ai-language-teacher-2026-09-22/EXPERIENCE.md`
- **Run at:** 2026-09-23T09:30:00Z

## Overall verdict

Discovery spines are honest and well-aligned with the four coached journeys, but they are **not yet a clean source-extract contract** for architecture or story-dev. Token `{path}` references resolve and calendar/lesson behavior is largely committed; load-bearing lesson chrome (chat bubble, mic, listening card visuals), contrast targets, NFR-3 connectivity error UX, and Progress/Settings/Living-plan journeys still force inventing. Treat as a strong coaching snapshot with labeled gaps — lock the thin slots before downstream build.

## Category verdicts

- Flow coverage — adequate
- Token completeness — adequate
- Component coverage — thin
- State coverage — adequate
- Visual reference coverage — adequate
- Bloat & overspecification — strong
- Inheritance discipline — strong
- Shape fit — adequate

## Findings by severity

### Critical (1)

**Component coverage** — Listening card missing DESIGN visual row (§ EXPERIENCE.md Component Patterns; Flow 2 / listening-check)

`Listening card` has strong behavioral rules but **no** DESIGN.md Components row.

Fix: Add visual anatomy (choice card, player chrome, hidden-then-reveal transcript).

### High (8)

**Flow coverage** — Progress journey has IA but no Key Flow (§ EXPERIENCE.md Key Flows; IA Progress row)

Progress (FR-15 / PRD Progress journey) has IA + Component Patterns but no Key Flow with climax.

Fix: Add Flow 5 — open Progress after a lesson/micro-lesson; climax = diagnosis + Living-plan CTA.

**Flow coverage** — NFR-3 connectivity failure un-narrated (§ PRD NFR-3; EXPERIENCE.md Open)

NFR-3 connectivity/API failure during a lesson has no Key Flow or failure beat. Open lists offline only.

Fix: Narrate retry → explicit error with next step (retry / «Пауза») inside Flow 2 or a short failure appendix.

**Token completeness** — No contrast targets for load-bearing pairs (§ DESIGN.md Colors)

No contrast targets for `ink`/`bg`, `muted`/`surface`, `on-coral`/`coral`, `missed`/`surface`, or dark counterparts. A11y deferred note does not waive token-intent contrast.

Fix: State WCAG AA ratios (or measured ratios) for those pairs in both modes.

**Token completeness** — chat-bubble and mic-control are comment stubs (§ DESIGN.md frontmatter components; Components section NOTES)

`chat-bubble` and `mic-control` frontmatter entries are comment stubs — no fill/radius/state colors.

Fix: Commit minimal visual tokens (fill, radius, resting/active) or mark inherited-platform with an inheritance note.

**Component coverage** — EXPERIENCE-only components lack DESIGN visuals (§ EXPERIENCE.md Component Patterns vs DESIGN.md Components)

Missing DESIGN visual rows: `Week / month switcher`, `Inline pronunciation feedback`, `History bottom bar`, `Onboarding step`, `Living plan document`, `Progress sections`, `Settings sections`, `Telegram result card`.

Fix: Add DESIGN rows (or explicit “behavior-only / platform chrome” inheritance).

**Component coverage** — Chat bubble / Mic control visuals unfinished (§ DESIGN.md Components; EXPERIENCE.md Component Patterns)

`Chat bubble` / `Mic control` exist on both spines but DESIGN visual rules are unfinished NOTES; EXPERIENCE has behavior.

Fix: Commit visual states so lesson stories are not free-form.

**State coverage** — Lesson connectivity/API error absent from State Patterns (§ PRD NFR-3; EXPERIENCE.md State Patterns / Open)

Lesson connectivity/API error (NFR-3) absent from State Patterns.

Fix: Add Lesson row: retry → explicit error + retry/«Пауза» — distinct from offline-out.

**Shape fit** — Discovery status with open NOTES fails implementation-contract bar (§ DESIGN.md / EXPERIENCE.md frontmatter status: discovery; memlog Finalize)

Status `discovery` with many open NOTES means load-bearing decisions are **not** all committed — fails the “implementation contract” bar while fitting Discovery shape.

Fix: Close chat/mic/listening visual, contrast, NFR-3, and Progress flow before architecture extract.

### Medium (14)

**Flow coverage** — First-run failure paths un-narrated (§ EXPERIENCE.md Flow 1 Open; Accessibility Floor)

Mid-wizard exit, consent refusal, mic deny, and speaking timeout are explicitly un-narrated.

Fix: At least one failure beat per gate (consent refuse; mic deny) so story-dev does not invent.

**Flow coverage** — Voice and Lesson-template climaxes collapsed (§ extract-prd journeys; Flow 2 step 6)

Voice and Lesson-template journeys (study-heavy / oral / transfer) collapse to “run by Lesson template” with no template-specific climax.

Fix: One short beat table per template (stage order + listening-card vs dialogue emphasis) or cite addendum bands as normative.

**Flow coverage** — Living plan and Settings lack Key Flows (§ EXPERIENCE.md IA + Component Patterns)

Living plan replan (FR-5) and Settings (NFR-4) are IA/components only — no Key Flow.

Fix: Optional short flows: see «план обновлён»; save Settings / «Привязать».

**Token completeness** — Typography tokens lack size/weight/lineHeight (§ DESIGN.md Typography NOTE)

Typography tokens lack `fontSize` / `fontWeight` / `lineHeight`.

Fix: Lock a minimal ramp or explicit “platform default sizes” inheritance table.

**Token completeness** — spacing.density is qualitative only (§ DESIGN.md Layout & Spacing)

`{spacing.density}: outlook-dense` is qualitative only — no numeric scale.

Fix: Define a dense tool scale (`1`–`6` or gutter/margin) before implementation stories.

**Component coverage** — Component name drift across spines (§ DESIGN.md vs EXPERIENCE.md)

Name drift: `CTA button (coral)` vs `CTA buttons`; `Numbered step circle` vs `Numbered plan steps`; `Chat bubble(s)`.

Fix: Align canonical names for extractors.

**Component coverage** — Accent rule is DESIGN-only (§ DESIGN.md Components)

`Accent rule` is DESIGN-only (motif under Numbered plan steps in EXPERIENCE).

Fix: Add EXPERIENCE behavioral row (when/where rules appear) or fold into Numbered plan steps explicitly.

**State coverage** — Cold-load / skeleton missing for full-screen surfaces (§ EXPERIENCE.md State Patterns)

Cold-load / skeleton missing for Calendar home, Lesson, Living plan, Progress, Settings.

Fix: One cold-load treatment per full-screen surface.

**State coverage** — Empty states unspecified for key surfaces (§ IA surfaces; Empty side panel only)

Empty Progress / empty Living plan / empty calendar (no lessons) not specified; only Empty side panel covered.

Fix: Short empty copy + next action per surface.

**State coverage** — Mic deny and consent refusal still Open (§ EXPERIENCE.md Accessibility Floor; Open)

Mic/permission-denied and First-run consent refusal called out as Open, not State Patterns.

Fix: Promote to State Patterns when locked.

**Visual reference coverage** — Spines link only pre-promote .working flows (§ EXPERIENCE.md IA; DESIGN.md Brand & Style)

Spines link only `.working/flow-calendar-home-2026-09-22.excalidraw` and `.working/flow-lesson-screen-2026-09-22.excalidraw`; `imports/template.psd` cited in DESIGN.md Brand & Style.

Fix: After promote, point to `wireframes/` / `mockups/` paths; keep spines-win.

**Visual reference coverage** — Orphan .working artifacts not inline-linked (§ .working/)

Orphans (pre-promote): direction HTML ×5 + index, `color-themes-hybrid-1-3.html`, PSD jpeg/slice/composite renders, capture-*.md — not inline-linked.

Fix: Promote winners into `mockups/`/`wireframes/` and link; leave rejects unlinked or archive.

**Inheritance discipline** — Platform defaults lack inheritance table (§ DESIGN.md Typography / Spacing NOTES)

“Platform-sensible defaults” for type size/spacing without an inheritance table leaves a hole.

Fix: Name the default owner (Electron/Chromium form controls vs custom) so consumers do not fork.

**Shape fit** — DESIGN omits numeric spacing/type typical of examples (§ DESIGN.md vs design-md-spec.md)

EXPERIENCE matches example section order; DESIGN includes `status`/`sources` beyond design.md-spec frontmatter (harmless) but omits numeric spacing/type typical of examples.

Fix: Either lock scales or keep explicit inheritance stubs.

### Low (12)

**Flow coverage** — Incomplete-resume exceeds PRD named UJs (§ EXPERIENCE.md Flow 4)

Incomplete-resume (Flow 4) is stronger than PRD named UJs (extra coverage).

Fix: None — keep.

**Token completeness** — today-tint has no dark pair (§ DESIGN.md Colors)

`{colors.today-tint}` has no dark pair (table shows —).

Fix: Document dark today treatment (omit tint / use `coral-soft-dark`) so dark mode does not invent.

**Token completeness** — All prose token refs resolve (§ DESIGN.md + EXPERIENCE.md)

All `{colors.*}`, `{typography.*}`, `{rounded.*}`, `{spacing.density}` prose refs resolve to frontmatter.

Fix: None.

**Component coverage** — Calendar event block + Side panel dual-covered (§ DESIGN.md Components; EXPERIENCE.md Component Patterns)

Calendar event block + Side panel are dual-covered with real rules.

Fix: None.

**State coverage** — Focus states omitted under deferred a11y (§ EXPERIENCE.md Accessibility Floor)

Focus states omitted — acceptable under deferred a11y.

Fix: None for Discovery.

**State coverage** — Calendar and lesson interaction states are strong (§ EXPERIENCE.md State Patterns)

Calendar selection / gates / pause / history / Telegram day-window states are strong.

Fix: None.

**Visual reference coverage** — mockups/ and wireframes/ directories absent (§ doc workspace root)

`mockups/` and `wireframes/` directories do not exist yet (expected until promote).

Fix: Create on promote.

**Visual reference coverage** — Spines-win-on-conflict stated (§ DESIGN.md Brand & Style; EXPERIENCE.md lead + IA)

Spines-win-on-conflict stated.

Fix: None.

**Visual reference coverage** — Unspecific direction HTML reference (§ DESIGN.md Brand & Style)

Unspecific “direction HTML” reference without paths.

Fix: Name locked hybrid artifacts or drop after promote.

**Bloat & overspecification** — Honest deferrals; complementary dual state lists (§ DESIGN.md / EXPERIENCE.md)

Honest `[NOTE FOR UX]` deferrals reduce fake precision; calendar state rules repeat across DESIGN/EXPERIENCE but stay complementary (visual vs behavioral).

Fix: Optional single cross-ref instead of dual state lists if length becomes a problem.

**Inheritance discipline** — No false UI-library inheritance (§ EXPERIENCE.md Foundation; DESIGN.md)

Correctly declares no named component library; Electron desktop + Russian chrome; does not invent shadcn/MUI tokens.

Fix: None.

**Shape fit** — Product shape fits IA and flows (§ EXPERIENCE.md IA + Key Flows)

Product shape (calendar home, gates, lesson, Telegram companion) fits IA and flows.

Fix: None.

## Reviewer files

- `review-rubric.md`
