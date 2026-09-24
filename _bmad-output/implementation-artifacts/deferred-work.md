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

