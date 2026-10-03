---
name: ai-language-teacher
status: final
updated: 2026-09-23
sources:
  - {planning_artifacts}/prds/prd-ai-language-teacher-2026-09-22/prd.md
  - {planning_artifacts}/prds/prd-ai-language-teacher-2026-09-22/addendum.md
---

# AI Language Teacher — Experience Spine

`DESIGN.md` is the visual identity reference; this spine is how the product behaves. Spines win on conflict with wireframes, mocks, or imports.

## Foundation

Electron desktop app. Form-factor: desktop primary. No named UI component library — chrome follows the working-tool visual language in `DESIGN.md`.

- **UI language:** Russian chrome. Lesson / teacher / material content is in the target language. UI language switching is deferred.
- **Dark mode:** Follow OS theme + manual override.
- **Motion:** Moderate transitions for panels and screens; respect OS reduce-motion.
- **Offline:** Out of v1 — no degraded-without-network lesson UX.
- **Accessibility:** Full a11y floor deferred (later concern).
- **Regulated language (in scope):** Privacy/PII copy aligned with NFR-1; explicit consent for microphone/voice recording and Telegram; AI disclaimer (not a certified teacher / not an exam guarantee); age/minors constraints via onboarding gating; no unqualified level or certificate claims.

## Information Architecture

| Surface                 | Reached from                                                                | Purpose                                                                                                         |
| ----------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Calendar home           | App open (post-onboarding); nav; exit from lesson/history; First-run climax | Outlook-like week (default) + month calendar of timed lessons; today orientation; side panel for preview / tips |
| Due gate overlay        | Cold open when a lesson is due / «сейчас»                                   | Choose «Начать урок» or «Перейти в календарь»                                                                   |
| Incomplete gate overlay | Cold open while a «Не завершен» lesson exists                               | Choose «Продолжить» or go to calendar                                                                           |
| Lesson                  | «Начать урок» / «Продолжить»; due-gate Start                                | Live dialogue/voice lesson with plan stages, mic, listening checks                                              |
| Lesson history          | Completed lesson → side panel «Открыть историю»; post-completion transition | Read-only lesson layout (header + left plan + dialogue tape); review then return to calendar                    |
| Onboarding wizard       | First open of desktop app                                                   | Step-by-step setup through placement and plan creation → calendar                                               |
| Living plan             | App nav/header; calendar side panel                                         | Full-screen document: goals / focus / upcoming topics; replan banner + change history                           |
| Progress                | App nav/header                                                              | Full-screen single-scroll dashboard (streak/XP → mastery → errors → words → Living plan link)                   |
| Settings                | App nav/header                                                              | Full-screen sections: Telegram, Voice, Schedule/duration, Goals/emphasis, LLM/API keys                          |
| Telegram micro-lessons  | Telegram (external companion)                                               | Daytime (~06:00–21:00 local) vocab translation micro-tasks + result card; reminders for due lessons             |

**Calendar side panel** (chrome of Calendar home, not a separate route): default hint when nothing selected; topic + short plan for next/missed/incomplete/future; CTAs per state; Living plan entry; First-run tip on how to start the first lesson.

→ Composition reference: `wireframes/flow-calendar-home-2026-09-22.excalidraw`, `wireframes/flow-lesson-screen-2026-09-22.excalidraw`; key mocks `mockups/key-calendar-home.html`, `mockups/key-lesson.html`, `mockups/key-connectivity-modal.html`, `mockups/key-lesson-history.html`, `mockups/key-progress.html`. Spines win on conflict.

**Spine-only surfaces** (no dedicated mock — build from tables): Due gate, Incomplete gate, Onboarding wizard, Living plan, Settings, Telegram micro-lessons.

## Voice and Tone

Microcopy. Brand mood and aesthetic posture live in `DESIGN.md` (working tool / дружеский).

| Do                                                                            | Don't                                                           |
| ----------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Friendly working-tool phrasing; clear next action                             | Kids language-app cheer, streaks-as-guilt, game coach tone      |
| Short Russian UI labels already decided («Начать урок», «Пауза», «Сохранить») | Sterile SaaS empty states and corporate filler                  |
| Regulated copy: consent, Privacy/PII, AI disclaimer — plain and explicit      | Unqualified certificate / level / “guaranteed exam pass” claims |
| Side-panel hint: «выберите урок для просмотра краткой информации или истории» | Cartoon encouragement on empty calendar                         |
| Replan banner: «план обновлён» + short summary                                | Hiding that the plan changed                                    |

## Component Patterns

Behavioral. Visual specs live in `DESIGN.md.Components` (tokens such as `{colors.coral}`, `{colors.coral-cta}`, `{colors.coral-soft}`, `{colors.missed}`, `{colors.done}`, `{colors.today-tint}`).

| Component                     | Use                                                  | Behavioral rules                                                                                                                                                                                                                                                                                                                               |
| ----------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Calendar event block          | Calendar home                                        | Timed hour-grid events (Outlook-like). States: completed (`{colors.done}`), scheduled, next (bold + `{colors.coral-soft}`), missed (`{colors.missed}` + exclamation), «Не завершен» (resumable; soft border treatment). Today marked separately (pill date + current-time line; faint `{colors.today-tint}` on today cell).                    |
| Week / month switcher         | Calendar home                                        | Default week; month available. Today / prev / next chrome.                                                                                                                                                                                                                                                                                     |
| Side panel                    | Calendar home                                        | Beside calendar (not modal). Empty: hint copy. Selection: topic + short plan. CTAs depend on state (see State Patterns).                                                                                                                                                                                                                       |
| CTA button (coral)            | Side panel, gates, lesson CTAs                       | Primary filled: «Начать урок», «Продолжить», and other coral primaries use `{colors.coral-cta}`. Lesson header also: «Завершить урок», «Пауза» (header actions may be secondary chrome). History exit: close/back (no complete/pause). Post-history: «Закончить» → calendar. Settings: «Сохранить»; Telegram «Привязать»; schedule «изменить». |
| Numbered plan steps           | Lesson left sidebar; Living plan / side panel motifs | Stage/step list; numbered `{colors.coral-cta}` circles + accent rules.                                                                                                                                                                                                                                                                         |
| Accent rule                   | Plan / side panel section headings                   | Short coral spark rule marking section starts; appears with numbered plan steps / panel labels.                                                                                                                                                                                                                                                |
| Chat bubble                   | Lesson + history                                     | Teacher and learner transcript. TTS play on teacher bubbles and material cards.                                                                                                                                                                                                                                                                |
| Inline pronunciation feedback | Under learner bubble                                 | Word/phrase issue + corrected model; present in live lesson and history replay.                                                                                                                                                                                                                                                                |
| Mic control                   | Lesson bottom bar                                    | Always visible. Default push-to-talk / hold-to-speak. Settings may enable auto-listen after teacher turn.                                                                                                                                                                                                                                      |
| Listening card                | Listening-check steps                                | Separate A/B/C choice card (not only inline under teacher). Player: play + scrubber + seek/replay + pause. Transcript/text hidden until after answer. Voice answer/retell also allowed; template/teacher selects modality per step.                                                                                                            |
| History bottom bar            | Lesson history                                       | Replaces live Mic control: lesson outcome / teacher short summary + template decision (study/oral/transfer). Audio replay for teacher TTS, learner recordings, listening materials.                                                                                                                                                            |
| Onboarding step               | Wizard                                               | One screen = one step. Outlook-like week slots on schedule step. Placement: briefing → written → listening → speaking. Plan-creation animation before calendar.                                                                                                                                                                                |
| Living plan document          | Living plan                                          | Sections: goals / focus / upcoming topics. No manual section edit; learner requests teacher replan. Banner «план обновлён» + change-history view.                                                                                                                                                                                              |
| Progress sections             | Progress dashboard                                   | Top→bottom: streak/XP → mastery → error themes → words/translation → Living plan link («что учитель усилит»). Inline expand; CTA to ask teacher / open Living plan.                                                                                                                                                                            |
| Settings sections             | Settings                                             | Telegram (link/unlink, reminders, micro-lessons); Voice (PTT vs auto-listen, mic device); Schedule/duration (summary + «изменить» mini-wizard); Goals/emphasis; LLM/API keys. Explicit «Сохранить» — not autosave-on-every-change.                                                                                                             |
| Telegram result card          | Telegram micro-lesson                                | Score correct/total; per wrong word: meaning + correct translation + error note (wrong translation or spelling). No separate spelling task type in v1.                                                                                                                                                                                         |

## State Patterns

| State                              | Surface             | Treatment                                                                                                                                                                                                |
| ---------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Empty side panel                   | Calendar home       | Hint: «выберите урок для просмотра краткой информации или истории»                                                                                                                                       |
| Next lesson selected               | Calendar side panel | Topic + short plan + «Начать урок» (`{colors.coral-soft}` emphasis on calendar event)                                                                                                                    |
| Missed selected                    | Calendar side panel | Topic + short plan + «Начать урок»; event uses `{colors.missed}` + exclamation                                                                                                                           |
| Future scheduled (not next/missed) | Calendar side panel | Topic + short plan; **no** «Начать урок»                                                                                                                                                                 |
| Completed selected                 | Calendar side panel | Preview first → «Открыть историю» → read-only lesson-layout history                                                                                                                                      |
| «Не завершен» selected             | Calendar side panel | Same as next/missed pattern: plan preview + «Продолжить» (not full history by default)                                                                                                                   |
| Today orientation                  | Calendar            | Distinct from next/missed: Outlook-like date pill + current-time line when today visible; `{colors.today-tint}` on today cell                                                                            |
| Mid-lesson pause / interrupt       | Lesson              | Header «Пауза» or window close: history saved, resumable; status «Не завершен». Auto-pause after prolonged absence (~15 min) = same as explicit «Пауза».                                                 |
| Connectivity / API error (NFR-3)   | Lesson              | Modal: «нет связи» (or equivalent plain copy) with **«Повторить»** \| **«Пауза»**. Lesson does not auto-abandon; «Пауза» → «Не завершен» path. Distinct from offline-out (no offline lesson mode in v1). |
| Due gate                           | Cold open           | Only when a lesson is due/now — not merely because a next lesson is scheduled. «Начать урок» \| «Перейти в календарь». Calendar branch keeps side panel preview + «Начать урок».                         |
| Incomplete gate                    | Cold open           | While «Не завершен» exists: «Продолжить» \| go to calendar                                                                                                                                               |
| Lesson → history transition        | Lesson              | On normal completion: marked completed; UI switches into read-only history mode for that lesson                                                                                                          |
| History mode                       | Lesson history      | Read-only; no «Завершить урок» / «Пауза»; close/back or «Закончить» → calendar                                                                                                                           |
| Placement stages                   | Onboarding          | Briefing → written (timer may end stage) → listening (play → questions) → speaking dialogue                                                                                                              |
| Plan creation                      | Onboarding          | Animation «создаём план обучения» → calendar + side panel first-lesson tip (no Living plan review step)                                                                                                  |
| Replan updated                     | Living plan         | In-page banner «план обновлён» + short summary; change-history view also available                                                                                                                       |
| Telegram day window                | Telegram            | Micro-lessons only ~06:00–21:00 local; never at night                                                                                                                                                    |
| Telegram linked/unlinked           | Settings            | Status after «Привязать» via external Telegram / deep-link (not manual chat-id entry)                                                                                                                    |
| Progress sync after micro-lesson   | Progress (silent)   | Stats update without bot CTA to open desktop Progress / Living plan                                                                                                                                      |

## Interaction Primitives

- **Pointer / keyboard:** Primary desktop input alongside voice; Outlook-like calendar navigation (view switch, today, prev/next).
- **Voice:** Push-to-talk / hold-to-speak by default; optional auto-listen after teacher turn (Settings).
- **Listening player:** Play, pause, scrub/seek, replay from position on listening cards and (in history) material replay.
- **Side panel selection:** Click calendar lesson → panel updates; does not navigate away from calendar until a CTA opens lesson or history.
- **Full-screen surfaces:** Living plan, Progress, Settings open as full screens (not drawers over calendar).
- **Settings save:** Explicit «Сохранить»; schedule edit via «изменить» opens mini-wizard reusing onboarding Outlook week-slots (not an inline grid on the settings page).
- **Telegram link:** «Привязать» opens external Telegram / deep-link.
- **Banned / deferred:** Offline lesson flow; full a11y instrumentation (later); UI language switch (later).

## Accessibility Floor

Behavioral. Visual contrast lives in `DESIGN.md`.

- **Reduce motion:** Honor OS reduce-motion; keep transitions moderate otherwise (panels/screens). Not highly expressive calendar/lesson motion; not near-zero animation.
- **Contrast (token intent):** Load-bearing pairs and measured ratios live in `DESIGN.md` Colors; filled CTAs use `{colors.coral-cta}` (not spark `{colors.coral}`) with `{colors.on-coral}`.
- **Deferred:** Full accessibility floor (labels, focus order, target sizes, screen-reader announcements for gates / mic / listening player) beyond token contrast intent — see Open.
- **Deferred:** Placement / speaking mic permission denial and related failure UX — not narrated; see Open.

## Inspiration & Anti-patterns

- **Lifted — Outlook 365 calendar:** Week columns, month grid, Today/prev-next chrome, view switcher, timed hour-grid events, today pill + current-time line — not a sparse dots calendar.
- **Lifted — Language Center PSD motifs:** Numbered coral circles, accent rules, warm adult-education mood; palette and clean sans. **Not** stock people/flags photography.
- **Rejected — Duolingo-kids / kids language-app UI:** Entertainment-game primary chrome.
- **Rejected — Sterile SaaS:** Generic dashboard emptiness; floaty multi-shadow product chrome.

## Responsive & Platform

- **Primary:** Electron desktop — calendar home, lesson, history, onboarding, Living plan, Progress, Settings.
- **Companion:** Telegram — lesson reminders (T−15 topic; at start time) and daytime micro-lessons; not a full desktop substitute.
- No mobile/web primary surface in v1 Discovery.

## Key Flows

### Flow 1 — First run (Денис, first open of desktop app)

1. Денис opens the app for the first time.
2. Greeting: how to address him + age → «Далее».
3. Learning goal + desired outcome → «Далее».
4. Interests / emphasis → lesson duration → schedule (Outlook week slots) → «Далее».
5. Consent: mic/voice recording; Telegram; AI disclaimer; Privacy/PII → «Далее». (Age stays on greeting only — not repeated on consent.)
6. Placement briefing: what the test is, how long, how scored, what it affects → «Далее».
7. Written test → «Далее» or stage timer ends.
8. Listening test: explanation → «Прослушать» → audio → questions → «Далее».
9. Speaking test: dialogue with the app → «Далее».
10. Plan-creation animation: «создаём план обучения».
11. **Climax:** Calendar home; side panel shows short guidance on how to start the first lesson — no Living plan review screen; no mandatory «Начать урок» as the climax.

**Open (not narrated):** exit mid-wizard; consent refusal; mic deny; speaking timeout.

### Flow 2 — Typical lesson (Денис, scheduled session)

1. T−15: Telegram reminder — lesson in 15 minutes on topic ….
2. At start time: Telegram — time to study; topic waiting.
3. Денис opens the desktop app.
4. **Due gate** (only if lesson is due/now): «Начать урок» \| «Перейти в календарь».
5. «Начать урок» → lesson screen. (If calendar: side panel keeps preview + «Начать урок».)
6. Greeting + short lesson-plan intro → lesson runs by Lesson template.
7. Plan done → farewell + next scheduled lesson date/time.
8. **Climax:** Lesson marked completed; UI switches into read-only history mode for that lesson.
9. Review history **or** «Закончить» → calendar home.

**Failure — connectivity / API (NFR-3):** If the network or API fails mid-lesson, show a **modal** «нет связи» with **«Повторить»** \| **«Пауза»**. Retry resumes the attempt; «Пауза» follows the incomplete path. Do not silently drop the lesson; this is not an offline lesson mode.

### Flow 3 — Between lessons / micro-lesson (Денис, Telegram)

1. Daytime (~06:00–21:00 local, never at night): micro-task arrives in Telegram.
2. Translate several words (new or review), L1→Target or Target→L1, word-by-word.
3. **Climax:** Bot result card — N correct of M; for each wrong word: meaning + correct translation + error note (translation or spelling).
4. Session ends in Telegram. Progress / error stats sync silently — no CTA to open desktop Progress or Living plan.

### Flow 4 — Incomplete resume «Не завершен» (Денис)

1. Mid-lesson external interruption (phone call); no return for >~15 min.
2. App auto-pauses (= explicit header «Пауза») → status «Не завершен».
3. On reopen while incomplete exists: gate «Продолжить» \| go to calendar — **or** from calendar: select lesson → side panel → «Продолжить».
4. Lesson screen: completed tasks visible; resume at the unfinished task (not restart from the beginning).
5. **Climax:** Finishes remaining work → normal completion → transition into history mode (same as Flow 2), not merely landing on the resumed task.

### Flow 5 — Progress diagnosis (Денис, after study)

1. Денис opens **Progress** from app nav/header.
2. Scrolls the single dashboard: streak/XP → mastery → error themes → words/translation.
3. Expands an item inline and/or follows the Living plan link («что учитель усилит»).
4. **Climax:** Clear next teaching action — ask the teacher to account for the gap **or** open Living plan — not streak alone as success.

## Open

- First-run failure edges (mid-wizard exit, consent refusal, mic deny, speaking timeout) — not narrated.
- Full accessibility floor — deferred beyond reduce-motion + DESIGN contrast targets.
- UI language switching — deferred.
- Offline lesson mode — out of v1 (connectivity errors during an online lesson are covered: modal «Повторить» | «Пауза»).
- Placement test internals may deepen later (scoring copy, exact timers beyond “timer may end written stage”).
- Live in-progress wording beyond locked interrupted status «Не завершен» not separately locked.
- Numeric type/spacing/shadow scales — deferred (platform-sensible / minimal elevation).
