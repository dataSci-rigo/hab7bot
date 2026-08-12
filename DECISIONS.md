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
- 2026-08-03: Phase 2 product-behavior calls (asked user, not assumed): web quick-add uses an
  inline role picker (no AI inference exists yet to default it); Inbox bulk actions cover
  role/project/quadrant/week + delete; Settings page for Phase 2 is a full layout with every
  SPEC-listed field visible, but only `week_start_day` is wired up — check-in times, model
  choice, Telegram pairing, and data export are disabled placeholders until their owning
  phase (4/5/6) lands.
- 2026-08-03: Added `MissionStatement` and `AppSettings` service layers + REST routes (`GET`/
  `PUT /api/v1/mission`, `GET`/`PUT /api/v1/settings`) in Phase 2, since the Roles & Goals
  mission editor and the Settings page needed them — this was deferred from Phase 1 per the
  decision above, and Phase 2 is where they're actually consumed.
- 2026-08-03: Added `POST /api/v1/tasks/{id}/uncomplete` (clears `status`→`planned` and
  `completed_at`→`null`) alongside the existing one-way `complete_task`. `TaskUpdate`
  deliberately excludes `completed_at` from client-settable fields, so the This Week board's
  "uncomplete" checkbox interaction had no correct way to revert a completed task without it.
- 2026-08-03: Inbox triage (single-row edits and bulk actions) auto-advances a task's status
  from `inbox` → `planned` when a role assigns it a project or a scheduled week — per SPEC's
  Inbox model ("anything captured without a week/project lands in the Inbox"), the inverse
  should hold: assigning either is what triaging *out* of the inbox means. Caught via manual
  browser verification — without this, triaged tasks correctly appeared on the This Week
  board but never left the Inbox list, so the same task showed in both places indefinitely.
- 2026-08-03: Added a big-rock pin toggle (star icon) to `TaskCard`, wired up only on the This
  Week board. Also caught via manual verification — SPEC's Phase 2 DoD requires "pick big
  rocks" as part of the manual weekly cycle, but nothing in the initial build exposed
  `is_big_rock` in the UI at all. Includes the spec'd soft limit: pinning a 4th big rock for a
  role in the same week shows a toast warning but doesn't block the action.
- 2026-08-03: Full manual weekly cycle (capture → triage → big-rock pin → drag-to-schedule →
  complete/uncomplete) verified against a live backend + frontend in a real headless-Chromium
  browser session (`playwright-core`, scratchpad-only devDependency, not added to the repo),
  not just `tsc`/unit tests — screenshots confirmed each state transition and
  `console --errors` was empty throughout.
- 2026-08-04: AI schemas resolve roles/projects by exact-match **name/title**, not id — the
  model can't know our UUIDs, so `CaptureInference`, `ProjectSuggestion`, and
  `InboxTriageItem` all echo back a `role_name`/`project_title_match`/`goal_title`, resolved
  server-side (`app/ai/resolve.py`) case-insensitively against real rows. An unmatched name is
  left unset rather than fuzzy-matched, so a bad guess degrades to "no suggestion" instead of
  silently attaching to the wrong role/project.
- 2026-08-04: `app/ai/client.call_tool` uses forced `tool_choice` and returns `None` on any
  failure (missing key, timeout, malformed response) rather than raising — every feature
  function (`breakdown_project`, `suggest_projects`, `infer_task_metadata`, `triage_inbox`)
  re-validates the raw dict against its Pydantic schema before returning, so a
  schema-mismatched response degrades the same way a network failure does.
- 2026-08-04: Per-call AI timeouts are tiered by expected output size, discovered via a real
  breakdown call timing out server-side at the original flat 30s (`anthropic.APITimeoutError`
  — Sonnet took 40–60s+ to generate a ~30-task, 6-milestone breakdown). Capture stays at 10s
  (Haiku, single-task, fast-path per SPEC §3.4); inbox triage and suggestions at 60s; project
  breakdown at 90s (largest structured output of the four).
- 2026-08-04: `/capture` (the one AI write-path) never fails: `services/capture.py` always
  creates the task, falling back to the first active role and Q2/inbox defaults if inference
  returns `None` or resolves nothing. This does still require at least one role to exist
  first — same precondition manual task creation has always had (`role_id` is a NOT NULL FK);
  AI degradation doesn't paper over a genuinely empty install.
- 2026-08-04: Web quick-add gained an "Auto (AI)" role option (`allowAiCapture` prop) that
  routes through `POST /capture` instead of a plain create — but only wired up on the Inbox
  page's box. The This Week and Project-detail quick-adds keep the Phase 2 manual-role
  behavior, since `/capture` doesn't accept the `scheduled_week`/`project_id` context those
  two need; AI-assisted capture only makes sense for the context-free case.
- 2026-08-04: Inbox "AI triage" is one batched tool call covering every inbox task at once
  (per SPEC §2.2.2's "pre-fills suggestions for the whole inbox in one call"), surfaced as a
  dismissible inline banner per task ("AI suggests: role · quadrant · project" with
  Apply/Dismiss) rather than auto-applying anything — matches SPEC's "user accepts/edits."
- 2026-08-04: All three AI features (breakdown, suggestions, capture) plus inbox-triage
  verified against the live Anthropic API (not just recorded fixtures) in a real browser
  session: breakdown produced and accepted a 33-task/6-milestone proposal, suggestions
  produced and accepted a real project, capture correctly cleaned a raw string into a titled,
  classified task, and inbox triage correctly classified both a seeded and a freshly-added
  task. Degradation was separately verified against a live server with `ANTHROPIC_API_KEY`
  overridden empty for one throwaway subprocess (not touching the real `.env`): capture still
  returned 201 with defaults, breakdown/suggestions/inbox-triage all returned a clean 503.
- 2026-08-05: Phase 4's conversational agent tool set covers SPEC §2.1's list minus
  `get_progress_analysis` and `add_reflection` — both back onto `WeeklyReview`/`analyze_week`,
  which don't exist until Phase 5, same "don't build ahead of the phase that owns it" pattern
  as the Phase 1→2 mission/settings deferral. Also split `breakdown_project`/`suggest_projects`
  each into a propose tool (read-only) + an accept tool (`accept_breakdown_tasks`,
  `accept_project_suggestion`) mirroring the REST API's propose/accept split — ground rule 3
  ("never write AI output straight to the DB") applies exactly the same way in the bot as in
  the web UI, so the agent has to see the proposal, then explicitly ask the model to resubmit
  what the user wants to keep as a second tool call.
- 2026-08-05: "Destructive-action confirmations" (SPEC §2.1) scoped to exactly two tools —
  `drop_task` and `abandon_project` — rather than a generic ">1 item" counter. SPEC's own
  Phase-4 tool list has no delete tool at all (status changes to `dropped`/`abandoned` are the
  only destructive paths available), so there's no natural multi-item batch case to gate on;
  every drop/abandon requires confirmation unconditionally rather than trying to track
  same-turn call counts.
- 2026-08-05: Confirmation is a two-phase, cross-message flow: when the model calls
  `drop_task`/`abandon_project`, `run_agent_turn` does NOT execute it — it returns a
  `pending_confirmation` dict and feeds the model a tool_result saying "waiting on the user"
  so it can wrap up its reply gracefully. The bot then sends a Confirm/Cancel inline keyboard;
  the actual `dispatch_tool` call only happens from the callback handler if the user taps
  Confirm. Simpler than pausing/resuming the tool loop mid-turn, at the cost of the
  confirmation surviving across turns only in memory (see next entry).
- 2026-08-05: Inline-keyboard callback state (capture-fix task/role references, pending
  confirmations) lives in an in-memory token registry (`app/bot/state.py`), not a DB table.
  Telegram caps `callback_data` at 64 bytes — too small for two UUIDs — so buttons carry short
  opaque tokens that resolve back to real values in process memory. Trade-off: a bot restart
  invalidates any in-flight fix/confirmation keyboards (tapping a stale button just says "this
  has expired"). Acceptable for a single-user bot; would need a DB-backed table if this ever
  needed to survive restarts or run multi-process.
- 2026-08-05: `ConversationMessage.created_at` switched from `server_default=func.now()` to a
  Python-side `datetime.now(UTC)` default — found via a genuinely failing test
  (`test_ai_unavailable_degrades_gracefully`), not by inspection. SQLite's `CURRENT_TIMESTAMP`
  only has 1-second resolution, so a user message and its assistant reply appended in the same
  turn could tie, making `get_recent_messages`' ordering silently wrong (assistant sorted
  before user). Only `ConversationMessage` was changed — other tables' `created_at` columns
  don't have same-entity, same-second ordering requirements, so weren't touched.
- 2026-08-05: Rolling conversation summarization keeps the last 10 raw messages verbatim and
  folds anything older into one summary once the window exceeds 20 messages
  (`WINDOW_SIZE`/`SUMMARIZE_KEEP` in `services/conversation.py`), via one Haiku call per fold.
  If that summarization call fails, the old messages are simply left in place for next time
  (not deleted) — degradation here means "window grows a bit past 20," never data loss.
- 2026-08-05: Agent tests use a hand-rolled `FakeModelClient` (queue of canned `Message`-shaped
  responses, `tests/fakes.py`) monkeypatched over `app.ai.agent.create_message`, rather than
  recorded-fixture JSON files like Phase 3's forced-tool-use tests. The conversational agent's
  interesting behavior is the *loop* (chaining tool calls across turns, confirmation gating,
  max-iteration fallback) rather than any single response's shape, so a scripted sequence of
  responses per test reads clearer than reconstructing that sequence from static fixtures.
- 2026-08-06: Renamed the Telegram env vars `config.py` reads from `TELEGRAM_BOT_TOKEN`/
  `TELEGRAM_ALLOWED_USER_ID` to `HAB7BOT_TELEGRAM_TOKEN`/`HAB7BOT_ALLOWED_USER_ID` (via
  `pydantic.Field(validation_alias=...)`), per the user. `hab7bot/.env` lives inside a shared
  `env_sync.py` master `.env` (`~/Documents/.env`) alongside credentials for several other
  Telegram bots (adhd-bot, todo_list, food, plants, praxis, etc.) under per-project `#`
  sections — plain `TELEGRAM_*` names read fine functionally (env_sync's sections already
  scope values per project, so there's no actual value collision) but are easy to visually
  mix up when scanning the master file by eye, which is what prompted the rename. Both
  `~/Documents/.env` and `hab7bot/.env` were edited directly with the real values rather than
  via `env_sync.py sync`, which rewrites *every* project's `.env` from master (and deletes any
  key not present there) — out of scope for a session scoped to "write only to hab7bot."
