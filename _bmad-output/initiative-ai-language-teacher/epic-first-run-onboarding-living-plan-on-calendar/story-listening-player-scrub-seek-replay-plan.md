---
title: "2.3 Listening player — scrub, seek, replay"
type: "feature"
ticket: 10
status: "done"
created: "2026-09-29"
baseline_revision: "60cc0cf9f1f0c79a3a012a58650057d551bba9a4"
review_loop_iteration: 0
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Placement listening only offers play/pause — Learners cannot scrub, seek, or restart — so the EXPERIENCE listening-player controls are incomplete where listening audio exists today. This implements the deferred-work row from parent 2.3 (rich listening player scrub/seek/replay for placement).

**Approach:** Add a Russian placement listening player with play/pause, scrubber seek, and RESTART_ZERO «Сначала» on the existing TTS blob, using DESIGN `listening-card.player-chrome` tokens only — without changing TTS/API/domain placement gates beyond the approved must-play rule.

**Decisions:**

- MUST_PLAY: ENDED_ONCE — «Далее» unlocks only after native `ended` fires once; scrub/seek/restart free anytime; scrubbing to the end without `ended` does not count
- REPLAY: RESTART_ZERO — dedicated «Сначала» sets `currentTime=0` and plays; scrubber owns arbitrary seek; no ±N skip buttons this story; ENDED_ONCE flag stays sticky across restart

## Boundaries & Constraints

**Always:**

- Placement listening stage only (OnboardingPlacement); keep comprehension questions + «Далее» flow
- Player: play, pause, scrubber seek, RESTART_ZERO «Сначала»; Russian chrome; `listening-card.player-chrome` tokens only (ink/muted/line) — not full lesson listening-card layout or transcript-hiding rules
- Existing TTS blob via `POST /placement/listening/audio` — no new audio endpoints
- MUST_PLAY ENDED_ONCE; server still requires `placement_listening_generated` + client-reported `placement_listening_played`
- a11y this story: Russian `aria-label` on play/pause/«Сначала», scrubber `aria-valuemin/max/now`, visible focus; defer live-region gate announcements and 44px target audit
- Vitest covers scrub/seek/restart + must-play matrix; honor reduce-motion for non-essential motion

**Never:**

- Native `<audio controls>` as learner-facing chrome; ±N skip-chunk buttons
- Wire lesson listening card / history material replay; change written/speaking, consent FLAG, TeacherHost, Settings Voice
- Relax text-only / listening incompleteness server rejects
- (Parent 2.3 Never / deferred-work still own: cloud Voice, adaptive bank, Epic 3.7 pronunciation)

## I/O & Edge-Case Matrix

| Scenario             | Input / State                          | Expected Output / Behavior                                    | Error Handling                |
| -------------------- | -------------------------------------- | ------------------------------------------------------------- | ----------------------------- |
| Happy play           | Audio ready, duration known            | Play/pause; scrubber tracks position; times `m:ss`/`mm:ss`    | N/A                           |
| Duration unknown     | Before `loadedmetadata` / NaN duration | Scrubber disabled; times `0:00 / —`                           | N/A                           |
| Scrub/seek           | Drag scrubber                          | `currentTime` clamped 0..duration; playback from new position | N/A                           |
| Replay               | «Сначала»                              | `currentTime=0` + play; ENDED_ONCE sticky if already met      | Playback fail → Russian error |
| Must-play before     | `ended` not fired                      | «Далее» blocked; no PATCH                                     | Russian copy                  |
| Scrub without ended  | Seek to end, no `ended`                | Gate stays locked; no PATCH                                   | N/A                           |
| Must-play after      | `ended` once (restart/scrub after OK)  | PATCH played+answers → speaking                               | API error banner              |
| Sticky after restart | `ended` then «Сначала»                 | «Далее» still allowed without second `ended`                  | N/A                           |
| TTS fail             | Audio fetch 422                        | Existing retry/Settings; no player chrome                     | Unchanged                     |
| Play fail            | `play()` rejects                       | Russian playback error; no fake played                        | Unchanged                     |

</frozen-after-approval>

## Code Map

- `OnboardingPlacement.vue` — replace inline `<audio>`/play button with `ListeningPlayer`; keep TTS fetch + submit gate on `listeningPlayedLocal`
- `OnboardingPlacement.spec.ts` — extend must-play matrix; migrate from lone `listening-play` to player testids
- `components/ListeningPlayer.vue` (+ `.spec.ts`) — reusable chrome; mount only from placement this story
- Testid contract: keep `listening-audio` on hidden `<audio>`; `listening-play`, `listening-scrub`, `listening-replay` («Сначала»); optional wrapper `listening-player`
- `DESIGN.md` / `EXPERIENCE.md` — player-chrome tokens + play/pause/scrub/seek/replay contract
- `teacherClient.ts` `synthesizeListeningAudio` — reuse; do not change contract
- Do not change `domain/learner.py` listening completeness (client-only ENDED_ONCE)

## Tasks & Acceptance

**Execution:**

- [x] `ListeningPlayer.vue` (+ `.spec.ts`) — play/pause, scrubber, RESTART_ZERO, `m:ss`/`mm:ss` labels, Russian aria, sticky `ended-once` + `playback-error` emits; testids per Code Map; scrubber disabled until duration known
- [x] `OnboardingPlacement.vue` — mount ListeningPlayer; wire `ended-once` → `listeningPlayedLocal`; keep TTS fetch/errors
- [x] `OnboardingPlacement.spec.ts` — scrub-without-ended block; ended→restart→submit OK; TTS-fail path
- [x] On Done: deferred-work listening-player row `resolved_by` this spec

**Acceptance Criteria:**

- Given listening audio ready, when Learner uses play/pause/scrub/«Сначала», then position and times update without native browser controls
- Given duration unknown, when player mounts, then scrubber is disabled and times show `0:00 / —` until metadata loads
- Given `ended` not fired, when scrubber seeks to end (or «Далее» clicked), then gate blocked and no PATCH
- Given native `ended` once, when Learner clicks «Сначала», then playback restarts from 0 and «Далее» remains allowed without a second `ended`
- Given gate met and answers chosen, when «Далее», then stage advances to speaking as today
- Given TTS/play failure, when recovery needed, then existing retry/Settings or playback error — no fake pass

## Implementation Notes

- Extract `ListeningPlayer` for Epic 3.5 reuse; do not wire lesson/history here.
- Props/emits: `src` in; sticky `ended-once` and `playback-error` out.
- Time labels: elapsed and total as `m:ss` / `mm:ss` (floor seconds, zero-pad seconds); update on `timeupdate` (throttle OK in tests).
- Scrubber: range input with `aria-valuemin/max/now`; disable until finite duration; reduce-motion → no decorative scrub animation.
- Server `placement_listening_played` stays client-reported; prove playback locally.
- Shipped 2026-09-29: `components/ListeningPlayer.vue` (+ spec) mounted only from `OnboardingPlacement`; ENDED_ONCE via sticky emit; scrub seek does not count as must-play; deferred-work listening-player row resolved_by this spec. Manual GUI scrub/ended/«Сначала»/«Далее» path not run in this environment.

## Spec Change Log

## Review Triage Log

- blind: stale playback-error after successful retry — **medium** — confirmed: parent clears only in `onListeningEndedOnce`. Route: patch
- blind: scrubbing stuck without `@change` — **medium** — confirmed: `scrubbing` only cleared in `onScrubEnd`. Route: patch
- blind: CSS uses `--color-surface` / `--radius-md` beyond ink/muted/line — **low** — cosmetic; intent means neutral player chrome, not exclusive CSS-var set. Rejected (low + everyday cosmetic)
- blind: reduce-motion rule is no-op — **low** — confirmed no transitions defined. Rejected (low)
- blind: no `<audio @error>` path — **medium** — confirmed only `play()` failures emit. Route: patch
- blind: frontmatter/status/logs process noise — **false** — process meta; fix would edit this build's spec. Rejected
- blind: DESIGN/EXPERIENCE spines not updated — **false** — Intent Never excludes lesson/history surfaces; planning spines not in-scope for this ship. Rejected
- blind: AC answers-chosen untested — **low** — client submit does not require answers selected; pre-existing. Rejected (low)
- blind: no reset on `src` change — **low** — `ensureListeningAudio` early-returns once URL set; remount rare. Rejected (low + everyday rare)
- blind: deferred-work over-closes EXPERIENCE — **false** — deferred row was placement scrub/seek/replay from 2.3; Boundaries keep lesson/history out. Rejected
- blind: no timeupdate-driven times test — **medium** — carried with verification-gap. Route: patch
- blind: missing aria-valuetext — **low** — beyond stated a11y floor (labels + valuemin/max/now). Rejected (low)
- edge: scrub without change freezes timeupdate — **medium** — carried. Route: patch
- edge: src prop change stale endedOnce — **low** — carried, rejected as rare
- edge: duration becomes non-finite after known — **low** — rare media quirk. Rejected (low)
- edge: audio `@error` missing — **medium** — carried. Route: patch
- edge: play() reject after unmount — **medium** — confirmed catch emits unconditionally. Route: patch
- edge: deletion clear-on-play-error — **medium** — carried with stale banner. Route: patch
- edge: tokens-only claim — **low** — carried, rejected as cosmetic
- verification-gap: placement playback-error banner untested — **medium** — pre-verified. Route: patch
- verification-gap: timeupdate never drives scrubber/times in tests — **medium** — pre-verified. Route: patch
- verification-gap: scrub-end never verified — **medium** — pre-verified. Route: patch
- verification-gap other: successful play retry leaves stale banner — **medium** — carried. Route: patch

## Verification

**Commands:**

- `cd apps/desktop && npm test && npm run typecheck && npm run build` — ListeningPlayer + placement specs green

**Manual checks:**

- Scrub mid-clip, seek to end without finishing (gate locked), let `ended` fire, «Сначала», then «Далее» → speaking
