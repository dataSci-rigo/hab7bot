# Compass — 7 Habits Weekly Planner

See `SPEC.md` for scope/domain model, `CLAUDE.md` for build phases and ground rules,
`DECISIONS.md` for technical decisions made along the way.

## Status

Phases 0–6 done (skeleton, domain/REST, web MVP, AI integration, Telegram bot, Google
Calendar/Tasks sync, proactive loops + weekly review). See `CLAUDE.md` for the full phase
plan. Phase 6's bot-side proactive jobs (morning brief/evening check-in/weekly
review/planning prompt) are code-complete and unit-tested but not yet verified against
the real Telegram bot — see the 2026-08-13 entry in `DECISIONS.md`.

## Local dev

Backend deps are managed via the conda env `p312` (see `DECISIONS.md`), not `uv` as
SPEC.md originally called for. `backend/requirements.txt` is the manifest of record.

```
make dev-api    # FastAPI on :8000 (reload)
make dev-web    # Next.js on :3000 (reload)
make dev-bot    # Telegram bot worker (long-polling)
make check      # ruff + pytest + frontend typecheck
make migrate    # alembic upgrade head
```

Copy `.env.example` to `.env` and fill in secrets before running anything that needs
Anthropic, Telegram, or Google sync.

For Google Calendar/Tasks sync, run `python -m scripts.google_oauth_setup` once,
locally (needs a browser — won't work over SSH/on a headless server), to authorize.

`docker-compose.yml` + Dockerfiles exist per the repo layout in CLAUDE.md but are
untested so far — Phase 0 was verified via `make dev`, not `docker compose up`.
