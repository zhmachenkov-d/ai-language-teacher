# Deferred work

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-scaffold-electron-vue-desktop-and-python-teacher-package.md`
  summary: Document Linux Electron system library needs (e.g. libatk) in AGENTS.md desktop start notes
  evidence: Electron failed here with missing libatk-1.0.so.0; review deferred because the fix edits AGENTS.md agent-context

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-scaffold-electron-vue-desktop-and-python-teacher-package.md`
  summary: Automated proof that desktop main/preload start without a live teacher beyond npm run build
  evidence: verification-gap — build would stay green if a hard teacher dependency were added; revisit with static coupling scan or smoke in 1.2 lifecycle

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-scaffold-electron-vue-desktop-and-python-teacher-package.md`
  summary: Party-mode memlog changes mixed into the 1.1 working tree
  evidence: `_bmad-output/party-mode/memories/installed/.memlog.md` is outside the story Code Map; keep memory, do not treat as scaffold deliverable when committing

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md`
  summary: Electron host-survival UX when the UI window closes (tray and/or hide-without-tray reopen/attach; teacher must not stop solely because the window closed)
  evidence: Split from 1.2 to keep the draft under the token budget; core loopback API + auth + spawn remains in-spec; AD-2 window-close gate moves here with the visible host model choice

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md`
  summary: Learner-visible stopped/error/retry chrome (copy language and UI) when teacher start/attach fails
  evidence: Split from 1.2 with host-survival UX; narrowed 1.2 proves lifecycle status + health over HTTP without polished status chrome (Story 1.4 may also own Russian chrome)

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md`
  summary: Electron thin-host spawn/attach/stop/status, userData token mint/load bridge, preload token/base_url surface, and Vue GET /health smoke when running
  evidence: Second split from 1.2 to fit the token budget; narrowed spec ships teacher loopback FastAPI + Bearer auth + health + pytest only

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md`
  summary: Strengthen AGENTS.md unauthenticated health smoke to assert error JSON body shape `{code,message,retryable}` not only HTTP status
  evidence: Review triage deferred because the fix edits agent-context AGENTS.md

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md`
  summary: When Electron token bridge lands, explicitly cover remint/rotate and invalidate-on-clear of prior Bearer tokens (epic Story 1.2 AC)
  evidence: Review found remint/rotation not parked beyond userData mint/load in deferred Electron spawn entry

## Deferred from: code review of spec-1-2-loopback-http-api-with-local-auth-and-electron-service-lifec.md (2026-09-24)

- Align older deferred-work evidence strings that still say Electron spawn / “lifecycle status” remains in-spec with the frozen Intent (API-auth only; Electron deferred)
- Add pytest (or install-time) resolution of `teacher-api` console script and/or `python -m teacher_service.adapters.api` so miswired entrypoints cannot stay green while direct `cli.main` tests pass
- CLI: catch `OSError` from `uvicorn.run` (e.g. port busy) and exit controlled with stderr instead of a raw traceback
