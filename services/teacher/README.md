# Teacher service

Installable hexagonal package (`teacher_service`) with loopback HTTP API + Bearer local auth.
See `AGENTS.md` for listen/verify commands. Electron lifecycle remains deferred.

```bash
uv sync
uv run pytest
export TEACHER_AUTH_TOKEN=...   # from env, not the repo
uv run teacher-api              # 127.0.0.1:8765
```
