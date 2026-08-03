# DECISIONS.md

Append-only log of technical decisions not dictated by SPEC.md. One line per decision, with date.

- 2026-08-01: Backend dependency management uses the existing conda env `p312` (pip installs
  already present there) instead of `uv`, per user preference. `backend/requirements.txt` is
  kept as the manifest of record (used by Docker builds and to track versions); `pyproject.toml`
  holds ruff/pytest config only, no build backend.
- 2026-08-01: Phase 0 DoD verified via `make dev` (api + web run natively against conda `p312`
  and local npm), not `docker compose up`. `docker-compose.yml` and both Dockerfiles are written
  per the spec'd repo layout but not yet exercised — revisit once there's more to containerize.
- 2026-08-02: All model/service/REST-CRUD work in Phase 1 covers exactly what the Phase 1
  paragraph in CLAUDE.md names — roles, goals, projects, tasks, week-plans (+ role week
  intentions) — not the full "standard CRUD for roles, goals, projects, tasks, week-plans,
  reviews, settings" list in SPEC §6, which aggregates across all phases. `MissionStatement`
  and `WeeklyReview` SQLAlchemy models + migration exist now (SPEC §1 asks for "all models"
  in Phase 1), but have no service layer or REST routes yet — those land with the web
  mission editor (Phase 2) and the weekly-review job (Phase 5) respectively.
- 2026-08-02: All primary keys are `uuid.UUID` (SQLAlchemy `Uuid` type) for every entity, not
  just Task as SPEC §1's table literally specifies — for consistency across the schema.
- 2026-08-02: `scheduled_week` is stored as a plain `String(8)` ISO-week string (e.g.
  "2026-W32") rather than a dedicated ISO-week type; `WeekPlan` rows are created lazily
  (`get_or_create_week_plan`) only when a role intention is first set for that week — a week
  with only scheduled tasks and no intentions has no `WeekPlan` row at all.
- 2026-08-02: TS client generated via `openapi-typescript-codegen` (`make generate-client`)
  and committed under `web/src/lib/api/` — there's no CI/build step yet to regenerate it, so
  committing keeps the client in sync by convention until Phase 6 adds automation.
  `backend/openapi.json` itself is the transient input to that generation and is gitignored.
