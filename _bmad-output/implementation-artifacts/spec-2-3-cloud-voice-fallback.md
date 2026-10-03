---
title: "2.3 Cloud Voice fallback behind VoicePort (AD-9)"
type: "feature"
created: "2026-09-29"
status: "done"
route: "dispatch"
review_loop_iteration: 0
baseline_commit: "6e43f6b9bdf7531360d8eadab4d070fb66f32d9a"
context:
  - "{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Placement and later lessons only have local CLI Voice — when `espeak-ng`/Whisper-CLI is missing or fails, learners hit hard `voice_unavailable` with no config-gated cloud path, despite AD-9 requiring optional cloud fallback behind the same VoicePort.

**Approach:** Keep `VoicePort` signatures and local-first default; add an optional cloud Voice adapter composed behind the same port, gated by Config so cloud never runs silently; placement listening/speaking keep REAL_STT / fail-closed semantics.

**Decisions:**

- FALLBACK_POLICY: LOCAL_THEN_CLOUD — try local first; on `VoiceUnavailableError` only, if cloud secret present (re-read per call), retry cloud for that call; other local exceptions must not fall through to cloud
- VENDOR: STUB_HTTP_CONTRACT — cloud adapter implements the Cloud HTTP contract below; unit tests mock HTTP; live vendor left to env/docs (no pinned production vendor SDK)
- CONFIG_SURFACE: SECRET_PLUS_API — `SECRET_CLOUD_VOICE_API_KEY` (`cloud_voice_api_key`) + `GET`/`PUT /config/voice` (cloud-key status only — not 2.7 mic/PTT prefs); no Desktop Settings Voice fields
- MODALITIES: BOTH — cloud fallback covers TTS and STT behind the same port

## Boundaries & Constraints

**Always:**

- Single VoicePort surface (`synthesize_speech` / `transcribe_audio`); UI never calls cloud voice directly
- Local-first; cloud only after local `VoiceUnavailableError` and only when `get_secret(SECRET_CLOUD_VOICE_API_KEY)` is non-empty **on that call** (no construct-time snapshot)
- Cloud + composite map transport/empty/auth failures to `VoiceUnavailableError` only (placement stays on `voice_unavailable`, not 500)
- Cloud TTS returns non-empty **WAV** bytes (placement wire `mime_type: "audio/wav"`); cloud STT returns non-empty transcript string
- Domain stays Voice-free; API + adapters own I/O; secrets via Config (OS permissions); NFR1 on cloud-bound metadata
- Wire `snake_case`; errors `{ code, message, retryable }`
- `/config/voice`: `GET` → `{ "configured": bool }`; `PUT` body `{ "cloud_voice_api_key": "<non-empty>" }` → `{ "configured": true }`; blank/whitespace → 422; never echo secret; Bearer required (LLM parity)

**Never:**

- Adaptive placement bank; pronunciation/intonation scoring (Epic 3.7); Settings mic PTT/device or cloud-key UI (2.7 / later)
- Bundled local engine packaging; Lesson SSE / LessonSession; Telegram; TeacherHost rewrite; pinning a live cloud vendor SDK
- Silent cloud use without Config gate; dual Voice stacks from Vue; changing placement scoring; using `/config/voice` for mic/PTT prefs

## I/O & Edge-Case Matrix

| Scenario                            | Input / State                      | Expected Output / Behavior            | Error Handling                 |
| ----------------------------------- | ---------------------------------- | ------------------------------------- | ------------------------------ |
| Local happy, cloud unset            | Local CLI OK; no secret            | Local path; zero cloud HTTP           | N/A                            |
| Local happy, cloud keyed            | Local CLI OK; secret set           | Local path only; zero cloud HTTP      | N/A                            |
| Cloud unset, local fail             | Local `VoiceUnavailableError`      | `voice_unavailable`; no cloud HTTP    | retryable; no fake pass        |
| Cloud keyed, local fail             | Local raises; secret present       | Cloud contract HTTP; WAV / transcript | N/A                            |
| Cloud keyed, local+cloud fail       | Both raise `VoiceUnavailableError` | `voice_unavailable`; no fabricate     | retryable envelope             |
| Cloud secret empty after local fail | Whitespace/missing secret          | Treat as unset — no cloud HTTP        | no silent partial              |
| PUT blank key                       | `cloud_voice_api_key` blank        | 422; secret unchanged                 | `{ code, message, retryable }` |
| Injected FakeVoice                  | `create_app(voice=…)`              | DI override; no composite forced      | N/A                            |

</frozen-after-approval>

## Code Map

- `ports/voice.py` — VoicePort + `VoiceUnavailableError`; module + Protocol method docs → local-first / optional cloud behind same port
- `adapters/voice/__init__.py` — `LocalVoiceAdapter` (Config-free); `CloudVoiceAdapter` (contract + per-call secret); `LocalThenCloudVoice` composite owns Config gate
- `adapters/config/layout.py` — allowlist `SECRET_CLOUD_VOICE_API_KEY = "cloud_voice_api_key"`
- `adapters/api/app.py` — `GET`/`PUT /config/voice` (LLM-shaped); `create_app` default = `LocalThenCloudVoice(local, cloud)`; keep `voice=` DI; placement routes unchanged on `app.state.voice`
- `tests/test_voice_adapter.py` + config/voice API tests — mock HTTP; local-then-cloud; local-success-no-cloud; both-fail; FakeVoice DI; `/config/voice` parity with LLM tests
- Desktop Settings Voice — leave shell
- Do not change domain/placement scoring, TeacherHost, or listening-player UI

## Tasks & Acceptance

**Execution:**

- [x] Config `SECRET_CLOUD_VOICE_API_KEY` + `GET`/`PUT /config/voice` — LLM-parity wire; gate without silent use
- [x] `CloudVoiceAdapter` (Cloud HTTP contract) + `LocalThenCloudVoice` — BOTH; per-call secret; `VoiceUnavailableError` only
- [x] `create_app` default wiring — compose from Config; keep `voice=` DI override
- [x] Pytest: local-only; cloud keyed + local OK (no HTTP); local-fail→cloud; both-fail; `/config/voice`; FakeVoice DI
- [x] On Done: annotate deferred-work cloud Voice row `resolved_by` this spec

**Acceptance Criteria:**

- Given cloud unset, when local Voice works/fails, then behavior matches today (no cloud HTTP)
- Given cloud keyed and local succeeds, when TTS/STT is requested, then local only (zero cloud HTTP)
- Given cloud keyed and local raises `VoiceUnavailableError`, when TTS or STT is requested, then cloud contract path runs via VoicePort and returns WAV / non-empty transcript
- Given local and cloud both fail, when placement audio/transcribe is requested, then `voice_unavailable` with no fabricated media/transcript
- Given `GET`/`PUT /config/voice`, when key is set/blank/unauthorized, then `{configured}` / 422 / 401 with no secret echo (LLM parity)
- Given tests inject FakeVoice, when API runs, then composite/cloud is not forced

## Implementation Notes

- 2026-09-29: `SECRET_CLOUD_VOICE_API_KEY` allowlisted; `CloudVoiceAdapter` + `LocalThenCloudVoice` in `adapters/voice/`; `GET`/`PUT /config/voice` LLM-parity; `create_app` default composite; FakeVoice DI preserved.
- Cloud contract: `POST /v1/tts` JSON→WAV (RIFF sniff), `POST /v1/stt` raw audio→`{transcript}`; failures → `VoiceUnavailableError`.
- Composite: local first; cloud only on `VoiceUnavailableError` when secret non-empty per call; other local exceptions do not fall through.
- Verified: `uv run pytest` voice + config/voice suites green (35); full teacher suite was 205 at implement time.
- Deferred-work cloud Voice row `resolved_by: spec-2-3-cloud-voice-fallback.md`.
- 2026-10-03 pre-ship patch: `_base_url` fail-fast (unset/default stub); AGENTS.md cloud Voice docs; PUT `/config/voice` RuntimeError→500 test.

## Spec Change Log

- 2026-09-29 pre-approve review: locked Cloud HTTP contract, WAV requirement, per-call secret, `VoiceUnavailableError` mapping, `/config/voice` wire + ACs, matrix row for cloud-keyed+local-OK (from needs-changes review)

## Review Triage Log

- blind: whitespace test never installs whitespace secret — **low** — FileConfig strips/rejects whitespace; `_cloud_keyed` strip is defensive for other ConfigPorts. Route: patch (FakeConfig `"  "` case)
- blind: create_app default never asserts `_cloud` is CloudVoiceAdapter — **medium** — confirmed `test_create_app_default_voice_is_local_then_cloud` only checks local half. Route: patch
- blind: TTS happy-path never asserts Content-Type application/json — **medium** — confirmed capture unused. Route: patch
- blind: no HTTP revoke/clear for cloud_voice_api_key — **false** — Intent SECRET_PLUS_API locks blank→422 (LLM parity); clear-key is not this ship
- blind: keyed + unset base URL waits ~30s on 127.0.0.1:9 — **medium** — intentional STUB default; everyday keyed-without-env footgun. Route: defer
- blind: AGENTS.md omits cloud_voice_api_key /config/voice — **medium** — agent-context edit. Route: defer
- blind: NFR1 requires scrubbing TTS text/STT audio — **false** — NFR1 is identity fields out of LLM prompts; placement script/audio is the Voice payload AD-9 allows when gated
- blind: get_secret RuntimeError not mapped to VoiceUnavailableError — **medium** — confirmed `_cloud_keyed`/`_api_key` propagate RuntimeError → placement 500. Route: patch
- blind: module docstring dropped REAL_STT packaging notes — **low** — reject (cosmetic; REAL_STT still on VoiceUnavailableError/Protocol)
- blind: STT unparseable body untested — **medium** — confirmed; mapping exists without test. Route: patch
- blind: VoiceConfigUpdate docstring says “status only” — **low** — misstates PUT body. Route: patch
- blind: deferred-work resolved_by without resolving artifact in diff — **false** — untracked `spec-2-3-cloud-voice-fallback.md` is in the review diff
- blind: composite discards local error when cloud fails — **low** — reject (cloud error is actionable; chaining not required)
- blind: no audit log on cloud fallthrough — **low** — reject (not in Intent; logging would add surface)
- edge: empty/whitespace TEACHER_CLOUD_VOICE_BASE_URL → ValueError `/v1/tts` — **medium** — reproduced `ValueError unknown url type`. Route: patch
- edge: non-UTF-8 STT body → UnicodeDecodeError — **medium** — `json.loads(bytes)` can raise UnicodeDecodeError outside except. Route: patch
- edge: IncompleteRead escapes `_open` — **medium** — not subclass of caught URLError/OSError. Route: patch
- edge: get_secret RuntimeError after local fail → 500 — **medium** — same as blind mapping gap. Route: patch (grouped)
- edge: claim VoiceUnavailableError-only falsified — **medium** — evidence = ValueError/UnicodeDecodeError/IncompleteRead/RuntimeError. Route: patch (grouped)
- verify-gap: create_app default cloud half untested — **medium** — pre-verified. Route: patch (grouped with blind)
- verify-gap: STT unparseable untested — **medium** — pre-verified. Route: patch (grouped)
- verify-gap: TTS Content-Type unasserted — **medium** — pre-verified. Route: patch (grouped)
- verify-gap: PUT /config/voice RuntimeError→500 untested — **low** — rare; GET covered; LLM same gap. Route: defer
- verify-gap other: whitespace test name mismatch — **low** — same as blind whitespace. Route: patch (grouped)

## Design Notes

Compose adapters behind one port. `LocalVoiceAdapter` stays Config-free; composite re-reads the cloud secret each call (LLM pattern).

**Cloud HTTP contract** (stdlib `urllib`; mock in tests):

- Base URL: `TEACHER_CLOUD_VOICE_BASE_URL` required for live cloud calls; unset/blank/`http://127.0.0.1:9` (doc stub) fail closed immediately — no urlopen. Tests set env or `base_url=`
- Auth: `Authorization: Bearer <cloud_voice_api_key>`
- TTS: `POST {base}/v1/tts` with JSON `{ "text": "<string>" }` → `200` body = raw WAV bytes (`Content-Type: audio/wav`); non-200 / empty / non-WAV → `VoiceUnavailableError`
- STT: `POST {base}/v1/stt` with body = raw audio bytes, headers `Content-Type: <mime_type>`, `Authorization` as above → `200` JSON `{ "transcript": "<string>" }`; missing/empty transcript or non-200 → `VoiceUnavailableError`
- Timeouts: ~30s; never fabricate audio/transcript on error

Audio bytes leave the machine only when the secret is set and local already failed (AD-4/AD-9).

## Verification

**Commands:**

- `cd services/teacher && uv run pytest` — green, including composite + `/config/voice` cases

**Manual checks (if no CLI):**

- Cloud unset + no local engine: placement still `voice_unavailable` (no cloud HTTP)
- `PUT /config/voice` then forced local fail: contract path covered by mocked pytest (live env optional)
