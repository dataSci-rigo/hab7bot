# DECISIONS.md

Append-only log of technical decisions not dictated by SPEC.md. One line per decision, with date.

- 2026-08-01: Backend dependency management uses the existing conda env `p312` (pip installs
  already present there) instead of `uv`, per user preference. `backend/requirements.txt` is
  kept as the manifest of record (used by Docker builds and to track versions); `pyproject.toml`
  holds ruff/pytest config only, no build backend.
- 2026-08-01: Phase 0 DoD verified via `make dev` (api + web run natively against conda `p312`
  and local npm), not `docker compose up`. `docker-compose.yml` and both Dockerfiles are written
  per the spec'd repo layout but not yet exercised — revisit once there's more to containerize.
