# CLAUDE.md — Instructions for Claude Code

You are building **Compass**, a self-hosted 7 Habits weekly planner. **Read `SPEC.md` first — it is the source of truth for scope, domain model, and architecture.** This file tells you how to work.

## Ground rules
1. **Follow the phase plan below in order.** Finish a phase (including its Definition of Done) before starting the next. If you believe a phase should change, say so and ask before deviating.
2. **Ask, don't assume**, when the spec is ambiguous on product behavior. For purely technical choices consistent with the spec, decide and note the decision in `DECISIONS.md` (create it; append-only log, one line per decision with date).
3. **Never write AI output straight to the database.** All AI proposals (breakdowns, suggestions, triage) go through an accept step, per SPEC §3.
4. **One service layer.** Domain logic lives in `backend/app/services/`. FastAPI routes and Telegram agent tools must both call it. If you find yourself duplicating logic between bot and API, stop and refactor into a service.
5. **Structured AI outputs via tool use only** (forced `tool_choice`), never regex-parsing prose. All Anthropic calls live in `backend/app/ai/`. Model IDs come from env (`ANTHROPIC_MODEL`, default `claude-sonnet-4-6`; `ANTHROPIC_MODEL_FAST`, default `claude-haiku-4-5`) — never hardcode model strings elsewhere. If unsure about current API details, check https://platform.claude.com/docs rather than relying on memory.
6. **Graceful AI degradation.** Any AI failure must leave the app usable: capture still creates an inbox task with defaults; the bot replies with a plain error line; the web shows a retry affordance. Wrap AI calls with timeouts and one retry.
7. **Migrations always.** Any schema change = Alembic migration in the same commit. Never `create_all` outside tests.
8. **Secrets** only via env. Maintain `.env.example` whenever a new variable appears. Never commit `.env` or the SQLite file.
9. **Tests are part of every phase**, not a final phase. Minimum bar: services and AI-schema validation unit-tested; API routes covered by httpx TestClient tests; bot agent tested with a faked Anthropic client (record/replay style fixtures). Don't test against the live API in CI.
10. **Commit style:** small commits, imperative subject, body explains why. Run `make check` (ruff + pytest + frontend typecheck) before declaring any phase done.

## Repository layout
```
compass/
├── SPEC.md, CLAUDE.md, DECISIONS.md, README.md
├── docker-compose.yml, Makefile, .env.example
├── backend/
│   ├── pyproject.toml            # uv-managed
│   ├── alembic/
│   └── app/
│       ├── main.py               # FastAPI app
│       ├── models/               # SQLAlchemy
│       ├── schemas/              # Pydantic
│       ├── services/             # domain logic (shared)
│       ├── api/v1/               # routes
│       ├── ai/                   # anthropic client, prompts/, tools/
│       ├── bot/                  # telegram entry, agent loop, handlers
│       └── scheduler/            # APScheduler jobs
└── web/                          # Next.js 15, App Router, TS
    └── src/{app,components,lib}
```

## Build phases

### Phase 0 — Skeleton & plumbing
Repo layout above; `uv` project; FastAPI hello + `/healthz`; SQLite via SQLAlchemy 2.x with WAL; Alembic wired; Next.js app scaffolded with Tailwind + shadcn/ui; docker-compose with `api`, `bot` (stub), `web`; Makefile (`dev`, `check`, `migrate`); CI-style `make check` green.
**DoD:** `docker compose up` serves web → hits API healthcheck; `make check` passes.

### Phase 1 — Domain core + REST
All models from SPEC §1 with migrations; services for roles/goals/projects/tasks/week-plans; REST CRUD + `GET /weeks/{iso}/plan`; session-cookie auth (`APP_PASSWORD`); OpenAPI → generated TS client in `web/src/lib/api`.
**DoD:** full CRUD via HTTP with auth; service-layer unit tests; seed script creates demo roles/goals/tasks.

### Phase 2 — Web MVP (plan & review loop without AI)
Pages: This Week board (drag-to-schedule, big-rock pinning, complete/uncomplete), Inbox triage, Roles & Goals (+ mission editor), Projects CRUD, Settings. No AI yet.
**DoD:** a full manual weekly cycle (capture on web → triage → pick big rocks → schedule → complete) works end-to-end in the browser.

### Phase 3 — Anthropic integration
`app/ai/` module: client wrapper, prompt files, tool-use schemas; implement §3.1 breakdown, §3.2 suggestions, §3.4 capture inference; wire into web (breakdown preview/accept UI, suggestions UI, quick-add inference, "AI triage" on Inbox); `POST /capture`.
**DoD:** all three features usable from web; schema-validation tests with recorded fixtures; degradation behavior verified by killing the API key in a test.

### Phase 4 — Telegram bot: capture + agent
python-telegram-bot v21 long-polling worker; allowed-user gate; quick capture with inference + inline fix keyboard; the conversational agent loop per SPEC §2.1 with the full tool set calling services; conversation history table with rolling window + summarization; destructive-action confirmations.
**DoD:** from Telegram alone: capture, query the week, break down a project, reschedule tasks, complete tasks — all conversationally; agent tests with faked model client.

### Phase 5 — Proactive loops + weekly review
APScheduler jobs (morning brief, evening check-in, Sunday review generation then planning prompt) with idempotency; §3.3 `analyze_week` + WeeklyReview records; web Weekly Review page + reflections; guided Sunday planning conversation in the bot producing a draft week plan.
**DoD:** simulated-clock tests prove jobs fire once and messages render; a full AI-assisted weekly cycle works via bot with web review.

### Phase 6 — Trends, polish, ship
Trends page (Recharts: Q2 %, big-rock rate, role share, capture vs. complete); JSON export; settings for check-in times/model/week start; Caddy TLS option in compose; README with setup guide (BotFather steps, env vars, deployment via Tailscale or Caddy); voice-note transcription via `faster-whisper` if time permits (optional — mark clearly if skipped).
**DoD:** fresh-machine install from README succeeds; `make check` green; demo data screenshot flow documented.

## Kickoff prompt (paste into Claude Code to start)
> Read SPEC.md and CLAUDE.md in full. Then execute Phase 0. Before writing code, reply with a short plan for the phase and any questions. After my go-ahead, build it, run `make check`, and report the Definition of Done status.
