# Spine Pair Review — ai-language-teacher

## Overall verdict
Discovery spines are honest and well-aligned with the four coached journeys, but they are **not yet a clean source-extract contract** for architecture or story-dev. Token `{path}` references resolve and calendar/lesson behavior is largely committed; load-bearing lesson chrome (chat bubble, mic, listening card visuals), contrast targets, NFR-3 connectivity error UX, and Progress/Settings/Living-plan journeys still force inventing. Treat as a strong coaching snapshot with labeled gaps — lock the thin slots before downstream build.

## 1. Flow coverage — adequate
Checked PRD named journeys from sources/extract (`Onboarding`, `Plan and lessons`, `Voice`, `Between lessons and Telegram`, `Progress`, three Lesson templates) plus coached Incomplete-resume against EXPERIENCE.md Key Flows 1–4 for protagonist, numbered steps, climax, and failure path.
### Findings
- **high** Progress (FR-15 / PRD Progress journey) has IA + Component Patterns but no Key Flow with climax (EXPERIENCE.md Key Flows; IA Progress row). *Fix:* Add Flow 5 — open Progress after a lesson/micro-lesson; climax = diagnosis + Living-plan CTA.
- **high** NFR-3 connectivity/API failure during a lesson has no Key Flow or failure beat (PRD NFR-3; EXPERIENCE.md Open lists offline only). *Fix:* Narrate retry → explicit error with next step (retry / «Пауза») inside Flow 2 or a short failure appendix.
- **medium** First-run failure paths explicitly un-narrated (mid-wizard exit, consent refusal, mic deny, speaking timeout) (EXPERIENCE.md Flow 1 Open; Accessibility Floor). *Fix:* At least one failure beat per gate (consent refuse; mic deny) so story-dev does not invent.
- **medium** Voice and Lesson-template journeys (study-heavy / oral / transfer) collapse to “run by Lesson template” with no template-specific climax (extract-prd journeys; Flow 2 step 6). *Fix:* One short beat table per template (stage order + listening-card vs dialogue emphasis) or cite addendum bands as normative.
- **medium** Living plan replan (FR-5) and Settings (NFR-4) are IA/components only — no Key Flow (EXPERIENCE.md IA + Component Patterns). *Fix:* Optional short flows: see «план обновлён»; save Settings / «Привязать».
- **low** Incomplete-resume (Flow 4) is stronger than PRD named UJs (extra coverage). *Fix:* None — keep.

## 2. Token completeness — adequate
Extracted DESIGN.md YAML tokens and every `{path.to.token}` in DESIGN.md + EXPERIENCE.md; verified definition, hex (and light/dark pairs), and contrast targets for load-bearing pairs.
### Findings
- **high** No contrast targets for load-bearing pairs (`ink`/`bg`, `muted`/`surface`, `on-coral`/`coral`, `missed`/`surface`, dark counterparts) (DESIGN.md Colors; a11y deferred note does not waive token-intent contrast). *Fix:* State WCAG AA ratios (or measured ratios) for those pairs in both modes.
- **high** `chat-bubble` and `mic-control` frontmatter entries are comment stubs — no fill/radius/state colors (DESIGN.md frontmatter `components`; Components section NOTES). *Fix:* Commit minimal visual tokens (fill, radius, resting/active) or mark inherited-platform with an inheritance note.
- **medium** Typography tokens lack `fontSize` / `fontWeight` / `lineHeight` (DESIGN.md Typography NOTE). *Fix:* Lock a minimal ramp or explicit “platform default sizes” inheritance table.
- **medium** `{spacing.density}: outlook-dense` is qualitative only — no numeric scale (DESIGN.md Layout & Spacing). *Fix:* Define a dense tool scale (`1`–`6` or gutter/margin) before implementation stories.
- **low** `{colors.today-tint}` has no dark pair (table shows —) (DESIGN.md Colors). *Fix:* Document dark today treatment (omit tint / use `coral-soft-dark`) so dark mode does not invent.
- **low** All `{colors.*}`, `{typography.*}`, `{rounded.*}`, `{spacing.density}` prose refs resolve to frontmatter. *Fix:* None.

## 3. Component coverage — thin
Extracted component names from DESIGN.md Components, EXPERIENCE.md Component Patterns, and in-flow usage; checked dual presence with real visual + behavioral rules.
### Findings
- **critical** `Listening card` has strong behavioral rules but **no** DESIGN.md Components row (EXPERIENCE.md Component Patterns; Flow 2 / listening-check). *Fix:* Add visual anatomy (choice card, player chrome, hidden-then-reveal transcript).
- **high** EXPERIENCE-only components missing DESIGN visual rows: `Week / month switcher`, `Inline pronunciation feedback`, `History bottom bar`, `Onboarding step`, `Living plan document`, `Progress sections`, `Settings sections`, `Telegram result card` (EXPERIENCE.md Component Patterns vs DESIGN.md Components). *Fix:* Add DESIGN rows (or explicit “behavior-only / platform chrome” inheritance).
- **high** `Chat bubble` / `Mic control` exist on both spines but DESIGN visual rules are unfinished NOTES (DESIGN.md Components; EXPERIENCE has behavior). *Fix:* Commit visual states so lesson stories are not free-form.
- **medium** Name drift: `CTA button (coral)` vs `CTA buttons`; `Numbered step circle` vs `Numbered plan steps`; `Chat bubble(s)` (DESIGN.md vs EXPERIENCE.md). *Fix:* Align canonical names for extractors.
- **medium** `Accent rule` is DESIGN-only (motif under Numbered plan steps in EXPERIENCE) (DESIGN.md Components). *Fix:* Add EXPERIENCE behavioral row (when/where rules appear) or fold into Numbered plan steps explicitly.
- **low** Calendar event block + Side panel are dual-covered with real rules. *Fix:* None.

## 4. State coverage — adequate
Walked every IA surface; expected empty / cold-load / focus / error / offline / permission-denied where applicable. Offline out of v1; full a11y deferred — not invented.
### Findings
- **high** Lesson connectivity/API error (NFR-3) absent from State Patterns (PRD NFR-3; EXPERIENCE.md State Patterns / Open). *Fix:* Add Lesson row: retry → explicit error + retry/«Пауза» — distinct from offline-out.
- **medium** Cold-load / skeleton missing for Calendar home, Lesson, Living plan, Progress, Settings (EXPERIENCE.md State Patterns). *Fix:* One cold-load treatment per full-screen surface.
- **medium** Empty Progress / empty Living plan / empty calendar (no lessons) not specified (IA surfaces; only Empty side panel covered). *Fix:* Short empty copy + next action per surface.
- **medium** Mic/permission-denied and First-run consent refusal called out as Open, not State Patterns (EXPERIENCE.md Accessibility Floor; Open). *Fix:* Promote to State Patterns when locked.
- **low** Focus states omitted — acceptable under deferred a11y (EXPERIENCE.md Accessibility Floor). *Fix:* None for Discovery.
- **low** Calendar selection / gates / pause / history / Telegram day-window states are strong. *Fix:* None.

## 5. Visual reference coverage — adequate
Listed `mockups/` (absent), `wireframes/` (absent), `imports/` (`template.psd`), and `.working/` artifacts; checked inline spine links and spines-win statement.
### Findings
- **medium** Spines link only `.working/flow-calendar-home-2026-09-22.excalidraw` and `.working/flow-lesson-screen-2026-09-22.excalidraw` (EXPERIENCE.md IA); `imports/template.psd` cited in DESIGN.md Brand & Style. *Fix:* After promote, point to `wireframes/` / `mockups/` paths; keep spines-win.
- **medium** Orphans (pre-promote): direction HTML ×5 + index, `color-themes-hybrid-1-3.html`, PSD jpeg/slice/composite renders, capture-*.md — not inline-linked (`.working/`). *Fix:* Promote winners into `mockups/`/`wireframes/` and link; leave rejects unlinked or archive.
- **low** `mockups/` and `wireframes/` directories do not exist yet (expected until promote). *Fix:* Create on promote.
- **low** Spines-win-on-conflict stated (DESIGN.md Brand & Style; EXPERIENCE.md lead + IA). *Fix:* None.
- **low** Unspecific “direction HTML” reference without paths (DESIGN.md Brand & Style). *Fix:* Name locked hybrid artifacts or drop after promote.

## 6. Bloat & overspecification — strong
Checked for redundant restatement, pixel theater, and premature implementation detail vs Discovery status.
### Findings
- **low** Honest `[NOTE FOR UX]` deferrals reduce fake precision; calendar state rules repeat across DESIGN/EXPERIENCE but stay complementary (visual vs behavioral). *Fix:* Optional single cross-ref instead of dual state lists if length becomes a problem.

## 7. Inheritance discipline — strong
Checked for false UI-library inheritance, platform notes, and delta-only discipline.
### Findings
- **low** Correctly declares no named component library; Electron desktop + Russian chrome; does not invent shadcn/MUI tokens (EXPERIENCE.md Foundation; DESIGN.md). *Fix:* None.
- **medium** “Platform-sensible defaults” for type size/spacing without an inheritance table leaves a hole (DESIGN.md Typography / Spacing NOTES). *Fix:* Name the default owner (Electron/Chromium form controls vs custom) so consumers do not fork.

## 8. Shape fit — adequate
Compared spine shape to examples (Quill/Drift) and to product form-factor: Discovery coaching pair, calendar-first desktop + Telegram companion.
### Findings
- **high** Status `discovery` with many open NOTES means load-bearing decisions are **not** all committed — fails the “implementation contract” bar while fitting Discovery shape (DESIGN.md / EXPERIENCE.md frontmatter `status: discovery`; memlog Finalize assumption). *Fix:* Close chat/mic/listening visual, contrast, NFR-3, and Progress flow before architecture extract.
- **medium** EXPERIENCE matches example section order; DESIGN includes `status`/`sources` beyond design.md-spec frontmatter (harmless) but omits numeric spacing/type typical of examples (DESIGN.md vs design-md-spec.md). *Fix:* Either lock scales or keep explicit inheritance stubs.
- **low** Product shape (calendar home, gates, lesson, Telegram companion) fits IA and flows. *Fix:* None.

## Mechanical notes
- Source paths in frontmatter resolve (`prd.md`, `addendum.md`).
- No Mermaid in either spine.
- Component naming inconsistencies: CTA button(s); Numbered step circle vs Numbered plan steps; Chat bubble(s).
- EXPERIENCE Component Patterns cites `{colors.coral}` for next emphasis; DESIGN specifies `{colors.coral-soft}` (+ bold) for next — soft conflict consumers may mis-resolve (EXPERIENCE.md Calendar event block row vs DESIGN.md calendar-event-block / Components).
- DESIGN frontmatter `components.chat-bubble` / `mic-control` are non-machine-token stubs (comments only).
- `spacing.density: outlook-dense` is not a CSS dimension token.
- Spines correctly state spines-win; composition refs still under `.working/` (pre-promote).
- Frontmatter complete for Discovery (`name`, `status`, `updated`, `sources`); DESIGN also has `description` + tokens.
- Incomplete («Не завершен») event fill still explicitly unlocked — consumers must not invent a new brand hue (DESIGN.md Colors NOTE).
