# Compass — 7 Habits Weekly Planner

See `SPEC.md` for scope/domain model, `CLAUDE.md` for build phases and ground rules,
`DECISIONS.md` for technical decisions made along the way.

## Status

Phase 0 — skeleton & plumbing. Done.

## Local dev

Backend deps are managed via the conda env `p312` (see `DECISIONS.md`), not `uv` as
SPEC.md originally called for. `backend/requirements.txt` is the manifest of record.

```
make dev-api    # FastAPI on :8000 (reload)
make dev-web    # Next.js on :3000 (reload)
make check      # ruff + pytest + frontend typecheck
make migrate    # alembic upgrade head
```

Copy `.env.example` to `.env` and fill in secrets before running anything that needs
Anthropic or Telegram.

`docker-compose.yml` + Dockerfiles exist per the repo layout in CLAUDE.md but are
untested so far — Phase 0 was verified via `make dev`, not `docker compose up`.
