---
title: "2.3 Placement — briefing, written, listening, speaking"
type: "feature"
ticket: 3
status: "done"
created: "2026-09-28"
baseline_revision: "b4d9c774c8c437b8f149f98ed8328ab1a6037e70"
review_loop_iteration: 0
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After consent, Learners land on a chrome-only placement stub with no briefing or written/listening/speaking tasks — Living plan difficulty cannot be seeded from real skills, and text-only onboarding could slip through (FR2, AD-17).

**Approach:** Replace the stub with a multi-stage Russian placement flow (briefing → written → listening → speaking), generate items via LLM, synthesize listening audio via local TTS, capture speaking via local STT, persist seedable outcomes, and hand off to a plan chrome stub for 2.4 — calendar stays gated until 2.6.

**Decisions:**

- VOICE: REAL_STT — local STT via VoicePort; speaking result seedable only after real capture+transcript; no stub pass
- CONTENT: LLM_GEN — LLM generates written/listening/speaking items; missing/invalid LLM Config blocks with clear copy + Settings path + retry
- LISTENING_AUDIO: TTS — listening audio synthesized via local Voice TTS (not bundled fixture)
- HANDOFF: PLAN_STUB — after `placement_complete` → `#/onboarding/plan` chrome stub for 2.4 (mirrors consent→placement)

## Boundaries & Constraints

**Always:**

- GATE: intake incomplete → wizard; !consent → consent; consent && !placement_complete → placement; placement_complete → plan stub; calendar only in 2.6
- Stages: briefing → written (timer may end) → listening (play/pause → comprehension) → speaking dialogue; one stage/screen; resume mid-placement
- Listening not playback-alone; listening/speaking gaps block `placement_complete`; mic/Voice fail → retry and/or Settings — no fake pass
- Local-first VoicePort STT+TTS; LLM via port; persist domain→SQLite; UI commands only; `{ code, message, retryable }`; NFR1 (no surname/postal/email/phone in LLM prompts)
- One LLM-generated item set per placement run; play/pause listening only (scrub/seek deferred)

**Never:**

- Living plan create/animation (2.4), plan document (2.5), calendar climax (2.6), Settings Voice product wiring (2.7)
- Cloud Voice fallback; rich scrub/seek player; adaptive re-take bank; pronunciation/intonation scoring (Epic 3.7)
- Lesson SSE/LessonSession; Telegram deep-link; calendar-as-onboarded; TeacherHost/Settings-LLM rewrite; change 2.2 consent FLAG semantics

## I/O & Edge-Case Matrix

| Scenario           | Input / State                    | Expected Output / Behavior                             | Error Handling                     |
| ------------------ | -------------------------------- | ------------------------------------------------------ | ---------------------------------- |
| Briefing           | consent_complete                 | What/how long/scored/affects; «Далее» → written        | null learner → wizard              |
| LLM/Config missing | open placement or generate       | Block with Settings path + retry; no silent fake items | retryable error envelope           |
| Written            | answers or timer ends            | Result stored; → listening                             | 401: no local-only advance         |
| Listening happy    | TTS play + comprehension answers | Listening result stored; → speaking                    | N/A                                |
| TTS/play fail      | audio fails                      | Retry then explicit Russian error; no listening pass   | result withheld                    |
| Speaking happy     | dialogue + local STT transcript  | Seedable speaking result stored                        | N/A                                |
| Mic/STT fail       | cannot capture/transcribe        | Retry and/or Settings; no `placement_complete`         | clear Russian copy                 |
| Text-only complete | missing listening or speaking    | Reject `placement_complete`                            | 422 `{ code, message, retryable }` |
| All done           | listening+speaking present       | Persist seedable outcome; GATE → plan stub             | N/A                                |
| Reopen mid / done  | partial or `placement_complete`  | Resume stage / plan stub — never calendar              | null → wizard                      |

</frozen-after-approval>

## Code Map

- `epic-2-context.md` / `epics.md` 2.3 — AC; FR2 / AD-17
- `spec-2-2-…` — GATE FLAG; placement stub; leave consent alone
- `onboarding/gate.ts` + `router/index.ts` — `placement_complete` → plan stub; RESUME routes; calendar gated
- `OnboardingPlacementStub.vue` → real multi-stage placement; add `OnboardingPlanStub.vue`
- `OnboardingWizard.vue` / `OnboardingConsent.vue` — chrome/load/retry patterns
- `teacherClient.ts` — placement fields + generate/submit calls
- `domain/learner.py` / `domain/placement.py` — stage enum + results + `placement_complete`; require consent; reject text-only
- `sqlite.py` — ALTER for placement (mirror consent columns)
- `ports/` + `adapters/voice/` — VoicePort local STT+TTS; `adapters/llm/` — LlmPort for item gen
- `adapters/api/app.py` + `tests/test_learner_api.py` — placement API + 422 matrix
- Vitest: gate, resume, Config block, TTS fail, mic/STT fail, text-only, plan-stub handoff
- Do not change TeacherHost spawn/attach/health or Settings LLM persist internals

## Tasks & Acceptance

**Execution:**

- [x] Domain + SQLite — placement stages/results + `placement_complete`; reject without listening+speaking; ALTER; require consent
- [x] LlmPort + VoicePort (local STT/TTS) + API — generate items, TTS audio, STT transcript; Config-missing + text-only 422 tests
- [x] `teacherClient.ts` — mirror placement + generate/submit
- [x] Placement UI — briefing, written+timer, listening play/pause→questions, speaking+PTT; Config/Voice error paths
- [x] Plan stub view + `gate.ts`/router — HANDOFF; calendar locked
- [x] Vitest + `uv run pytest` + `npm test` + `npm run build`
- [x] On Done: sprint-status 2-3 → review; 2-2 → done if still `review`

**Acceptance Criteria:**

- Given consent_complete and LLM Config ready, when placement runs, then briefing→written→listening(TTS+comprehension)→speaking(STT) and results persist
- Given missing LLM Config or Voice/TTS/STT failure, when recovery is needed, then Settings/retry path — no fake complete
- Given missing listening or speaking, when complete is requested, then 422 and GATE stays on placement
- Given all stages complete, when persisted, then outcome is seedable for 2.4 and GATE opens plan stub — not calendar

## Implementation Notes

- 2026-09-28: `domain/placement.py` (new) — stage enum, `ChoiceItem`/`ListeningContent`/`PlacementItems`, `parse_placement_items` (strict-shape validation, no fabricated fallback), `placement_items_to_storage`/`placement_items_public` (server-only `correct_index` never reaches the wire), `score_choice_answers`, `score_speaking_transcript` (MVP word-count aggregate — explicitly not pronunciation/intonation scoring, deferred to 3.7).
- `domain/learner.py` — 11 new `Learner` fields (`placement_stage`, `placement_items`, written/listening answers+scores, `placement_listening_generated`/`_played`, speaking transcript+score, `placement_complete`). `update_learner` scores written/listening answers server-side from the persisted item set (client never supplies a score); `_require_placement_stage`/`_require_placement_complete` mirror 2.2's consent gating — reject any placement field without `consent_complete`, reject stage advances without the prior stage's result, and reject `placement_complete=true` without written+listening+speaking present (`placement_written_incomplete` / `placement_listening_incomplete` / `placement_speaking_incomplete` / `placement_requires_consent` codes). `placement_listening_generated` (server-only, set by the real TTS call) is required alongside client-reported `placement_listening_played`, so the listening gate can't be faked by PATCH alone.
- `ports/llm.py` + `adapters/llm/OpenAiLlmAdapter` — real OpenAI-compatible `/chat/completions` call over stdlib `urllib` (no new runtime dependency); raises `LlmGenerationError` on missing key/network/unparseable response — never fabricates items. `ports/voice.py` + `adapters/voice/LocalVoiceAdapter` — shells out to a configurable local TTS/STT CLI (`espeak-ng`/Whisper-CLI-shaped by default, env-overridable); raises `VoiceUnavailableError` when the engine is missing/fails.
- `adapters/api/app.py` — `POST /placement/items` (consent-gated, Config-gated, one-set-per-run cache, strips `correct_index` from the response), `POST /placement/listening/audio` (real TTS, marks `placement_listening_generated`), `POST /placement/speaking/transcribe` (real STT, persists transcript+score directly — never client-supplied); `PATCH /learner` extended for stage/answers/`placement_complete` only (transcript/score/items/generated-flag stay server-only). `create_app` takes optional `llm`/`voice` DI params (same pattern as `store`/`config`) so tests inject fakes instead of hitting network/audio hardware.
- `teacherClient.ts` — `PlacementStage`/`PlacementItemsPublic` types, extended `LearnerProfile`/`LearnerPatch`, `generatePlacementItems`/`synthesizeListeningAudio`/`transcribeSpeakingAudio`.
- `gate.ts` — `gateDestination` now requires `placement_complete`; consent-done-but-not-placement-done → `onboarding-placement`; `placement_complete` → new `onboarding-plan` stub (never calendar). `router/index.ts` adds `/onboarding/plan`; `OnboardingPlacementStub.vue` replaced by real `OnboardingPlacement.vue` (briefing → written-with-timer → listening play/pause+comprehension → speaking record/STT, each with Config/Voice/mic error banners + Settings links); new chrome-only `OnboardingPlanStub.vue` for the 2.4 handoff.
- Verified: `uv run pytest` (117, incl. 23 new domain + 16 new API placement tests), `npm test` (136, incl. 8 new `OnboardingPlacement.spec.ts` + extended gate/teacherClient/App/Consent specs), `npm run typecheck`, `npm run build` — all green. Manual GUI smoke (Electron/VNC) not run in this environment.
- Test-infra fix (unrelated regression surfaced by turning the placement stub real): `OnboardingConsent.spec.ts`'s `mountConsent` set `window.location.hash` _after_ `createRouter(...)`; a leftover hash from a prior test made the new router's initial navigation resolve against the stale route before the intended one, double-consuming a single mocked `Response` body. Fixed by setting the hash before router construction.
- Risk / follow-up: `LocalVoiceAdapter` needs a real `espeak-ng`/Whisper-CLI-shaped binary on the target machine — neither ships bundled, so on a fresh install `/placement/listening/audio` and `/placement/speaking/transcribe` will return `voice_unavailable` until an engine is present (or `TEACHER_TTS_COMMAND`/`TEACHER_STT_COMMAND` are pointed at one). Bundling a local engine under `ConfigPort.voice_models_dir()` is tracked as 2.7-adjacent follow-up, not done here (out of scope per 2.7 boundary). Speaking capture uses click-to-start/click-to-stop (not literal press-and-hold PTT) per Design Notes; real mic/speaker manual smoke was not exercised in this sandboxed devcontainer (no audio hardware).

## Spec Change Log

## Review Triage Log

- blind: Vue files under wrong `src/renderer/...` paths vs apps/desktop — **false** — `git diff --no-index` from `/dev/null`; files live at `apps/desktop/src/renderer/...` and Vitest discovers them
- blind: domain/placement, ports.llm/voice, tests absent from diff — **false** — untracked files are in the staged unified diff (`domain/placement.py`, `ports/llm.py`, `ports/voice.py`, placement tests)
- blind: spec-2-3 artifact missing from diff — **false** — untracked `spec-2-3-…md` is included in the review diff
- blind: non-briefing stage + null items → false «завершена» screen — **medium** — confirmed: `v-else` at end of template when `stage && !items` after failed regenerate. Route: patch
- blind: hydrateItems drops saved written/listening answers — **medium** — confirmed: always maps to `-1`. Route: patch
- blind: written timer always restarts at 05:00 on resume — **low** — confirmed; remaining time not persisted. Rejected (low + everyday rare mid-written crash; fix needs persist model complexity)
- blind: listeningPlayedLocal only / server trusts client played flag — **low** — UI gate is intentional; server cannot prove playback without media telemetry. Rejected (low + non-trivial proof pipeline)
- blind: listening/speaking voice endpoints skip consent_complete — **medium** — confirmed: only `/placement/items` checks consent. Route: patch
- blind: SpeakingAudioIn.audio_base64 unbounded — **medium** — confirmed no max size. Route: patch
- blind: listening control label English `Play / Pause` — **low** — confirmed. Route: patch (trivial copy)
- blind: briefing «четыре части» mis-counts stages — **low** — cosmetic copy. Route: patch (trivial)
- blind: no happy-path listening play→submit UI test — **medium** — carried with verification-gap listening gate. Route: patch
- blind: LLM system prompt hardcodes English despite target_language/l1 args — **low** — v1 pair is en/ru; user prompt still receives langs. Rejected (low + everyday matches v1 defaults)
- blind: sprint bumps 2-2 to done in 2-3 diff — **false** — intentional On Done task after merged/approved 2-2
- edge: non-briefing + null items → false complete — **medium** — carried same as blind. Route: patch
- edge: stage=complete && !placement_complete stuck without finish CTA — **medium** — confirmed: complete stage skips speaking template; finish only on speaking. Route: patch
- edge: hydrate drops answers — **medium** — carried. Route: patch
- edge: MediaRecorder construct/start throws after getUserMedia leaves tracks open — **medium** — catch sets micError without stopping stream. Route: patch
- edge: second record click while getUserMedia pending — **medium** — no in-flight guard. Route: patch
- edge: HTMLAudio play() rejection swallowed — **medium** — `.catch(() => undefined)` hides playback failure. Route: patch
- edge: voice endpoints without consent — **medium** — carried. Route: patch
- edge: concurrent POST /placement/items race — **low** — rare; cache path exists after first write. Rejected (low + everyday rare)
- edge: corrupt placement_stage from SQLite — **low** — update path validates enum; corrupt legacy row unlikely. Rejected (low)
- edge: TTS/STT command `.format` KeyError bypasses VoiceUnavailableError — **medium** — confirmed uncaught. Route: patch
- edge claim: STT failure lacks Settings/retry control — **medium** — speakingSaveError is text-only; TTS path has Settings link. Route: patch
- edge claim: speaking+PTT not press-and-hold — **false** — Design Notes / Implementation Notes explicitly defer hold-PTT to 2.7; click-toggle is intended
- verification-gap: GET/PATCH /learner never asserts answer-key strip — **medium** — pre-verified. Route: patch
- verification-gap: listening must-play UI gate untested — **medium** — pre-verified. Route: patch
- verification-gap: speaking record→STT UI path untested — **medium** — pre-verified. Route: patch
- verification-gap: transcribeSpeakingAudio return value unasserted — **medium** — pre-verified. Route: patch
- verification-gap other: real OpenAiLlmAdapter/LocalVoiceAdapter never executed in tests — **medium** (unverified severity for fabricate-on-error) — defer; settle with a thin adapter unit test or integration smoke later

## Design Notes

- Explicit `placement_complete` FLAG (mirror 2.2); server enforces listening+speaking seedable presence.
- Stage enum `briefing|written|listening|speaking|complete` for RESUME.
- Speaking PTT hold/press until 2.7 Voice prefs; score = transcript + simple aggregate (not pronunciation UI).

## Verification

**Commands:**

- `cd services/teacher && uv run pytest` — placement gates + Config/text-only 422 green
- `cd apps/desktop && npm test && npm run build` — gate/placement Vitest + build green

**Manual checks:**

- Consent → full placement → plan stub; Config missing → Settings path; TTS/mic fail retry; reopen mid-stage; `/` never calendar
