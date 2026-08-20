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
- 2026-08-12: Phase 4 fully verified live against the real Telegram API (not just the faked-
  model-client test suite): fast capture + inline fix keyboard (quadrant buttons, big-rock
  toggle, role picker), conversational week query, project breakdown + a real multi-milestone
  proposal, task rescheduling, task completion, and the drop/confirmation flow — the last one
  surfaced organically during a multi-turn negotiation ("tidy up first" → agent proposed
  dropping duplicate captures → user refined the ask → confirmation keyboards sent → user
  confirmed → task `status` flipped to `dropped`), which exercised the confirmation gating
  more thoroughly than the planned single-item test would have. Zero unhandled exceptions in
  the bot's log across the whole session.

  Two real bugs surfaced by this live testing (neither caught by the unit test suite, since
  both were gaps in what the tests exercised rather than logic errors in what they covered):
  1. **Missing `list_projects` tool** — the agent could look up a task's id by name
     (`list_tasks`/`search_tasks`) but had no equivalent for projects, so
     `breakdown_project`/`update_project`/`abandon_project` were unreachable from
     conversation by name. Added `list_projects` (schema, dispatch handler, persona guidance,
     test) mirroring the tasks pattern.
  2. **Inbox-status invariant was frontend-only.** The Phase 2 rule ("assigning a project or
     week means leaving the inbox," 2026-08-03 entry) lived solely in the web `Inbox` page's
     `patchAndTriage` wrapper — the Telegram agent's `update_task` calls went straight to
     `tasks_service.update_task` and bypassed it, so a task rescheduled by chat kept
     `status=inbox` forever, reproducing the exact web-only bug (task visible on This Week
     *and* stuck in the Inbox list) through a surface that never had the fix. Moved the
     invariant into `tasks_service.update_task` itself — advances `inbox`→`planned` when
     `project_id` or `scheduled_week` is set and the caller didn't also explicitly set
     `status` in the same call — so it now applies regardless of which surface makes the
     change. Removed the now-redundant frontend wrapper in `inbox/page.tsx` (both the
     per-row `patchAndTriage` and the bulk-update's manual `status` set) rather than leaving
     dead duplicate logic. Added 4 service-layer tests covering the invariant, including that
     an explicit `status` in the same call isn't overridden and that non-inbox tasks aren't
     reopened by a reschedule.
- 2026-08-12: Amended `SPEC.md` and `CLAUDE.md` per the user to bring Google Calendar/Tasks
  sync into v1 scope (it was previously an explicit §7 non-goal). Documentation only in this
  commit — no sync code written yet, that's the new Phase 5. Design borrows directly from
  `semantic_task_manager/{google_tasks.py,oauth_setup.py,sync.py}`, a working two-way Google
  Tasks sync already proven in that project (same OAuth client-secret file, same
  push-then-pull-then-conflict-resolve ordering, same link-table pattern) — chosen over a
  from-scratch design specifically because it's already validated. Key departures from that
  reference, both explicit user calls: (1) Compass-specific fields that don't exist in Google
  Tasks (role, quadrant, is_big_rock, project) get serialized into the synced item's `notes`
  field rather than dropped, so nothing is lost on a round-trip; (2) Calendar sync is full
  two-way (push scheduled tasks as events *and* pull unlinked events back as new,
  AI-classified tasks), not the simpler one-way push that was the starting proposal.
  Sequenced as a new Phase 5 (renumbering the old Phase 5→6, 6→7) specifically because it
  needs to register the bot worker's first scheduled job, which the old Phase 5 (proactive
  loops) would otherwise have introduced — better to introduce that infrastructure once, in
  the phase that actually needs it first, than twice. `google-auth`/`google-auth-oauthlib`/
  `google-api-python-client` will install into `p312` when Phase 5 is built (checked `rs313`
  first per the user's suggestion — it already has those 3 packages, but is Python 3.13 and
  missing SQLAlchemy/Alembic/ruff, so not a clean fit; ruled out rather than fragmenting
  hab7bot's backend across two conda environments).
- 2026-08-12: Phase 5 implemented. `google-auth`/`google-auth-oauthlib`/`google-api-python-client`
  installed into `p312` (pinned to the exact versions already validated in `rs313` against the
  same client-secret file, rather than picking fresh ones); this upgraded `protobuf` 3.20.3 →
  7.35.1 in that shared env — `pip check` and full `make check` both stayed green afterward, no
  other project in `p312` appeared to pin protobuf tightly, but worth knowing if something odd
  turns up elsewhere later.
- 2026-08-12: Added `Task.updated_at` (Python-side `default`/`onupdate`, not `server_default` —
  same reasoning as the `ConversationMessage.created_at` fix from Phase 4: SQLite's
  `CURRENT_TIMESTAMP` only has 1-second resolution, and last-write-wins sync needs a reliable
  ordering). Wasn't needed before Phase 5 since nothing previously compared "has this row
  changed" — `_push_task_updates` in `sync.py` is the first thing that does. The migration adds
  it with a `server_default=CURRENT_TIMESTAMP` (DDL-level, backfills existing rows) even though
  the ORM model itself only declares a Python-side default — deliberately asymmetric, matching
  how `created_at` mixins already work elsewhere in this codebase.
- 2026-08-12: `google_sync_enabled` lives on `AppSettings` (the DB-backed, user-editable model)
  — not `app/config.py`'s env-based `Settings`, where I put it by mistake on the first pass
  before catching it (SPEC's "`Settings` gains `google_sync_enabled`" meant the domain model,
  same class `week_start_day` already lives on). `AppSettingsUpdate` became a partial update
  (`week_start_day`/`google_sync_enabled` both optional) rather than adding a second PUT
  endpoint, matching the `TaskUpdate`/`exclude_unset` pattern already used everywhere else.
- 2026-08-12: Google sync deliberately excludes `status=dropped` tasks from being pushed at all
  (checked in `_push_new_tasks`/`_push_new_events`) — "dropped" is Compass's version of
  deleted, so a task the user dropped shouldn't reappear in Google Tasks/Calendar. Sync never
  deletes anything on the Google side even for tasks dropped *after* they were already synced
  (no delete call exists in `tasks.py`/`calendar.py`) — matches the reference
  implementation's scope (it doesn't implement delete either) and avoids sync accidentally
  destroying data the user might want to keep on the Google side regardless of Compass's state.
- 2026-08-12: Added `TaskOrigin.google` for tasks/events pulled in via sync. No migration
  needed — `TaskOrigin` uses `Enum(..., native_enum=False)`, so it's stored as a plain string
  column with no DB-level CHECK constraint; adding an enum member is a pure Python-side change.
- 2026-08-12: Task has no time-of-day field (only `scheduled_day`), so pushing to Calendar
  needed a rule for what kind of event to create: an all-day event if the task has no
  `estimate_minutes`, otherwise a timed event starting at a fixed default (9am local) running
  for `estimate_minutes` — the least-arbitrary anchor available given the data actually on
  hand. Documented in `calendar.py` as `DEFAULT_START_HOUR`, easy to revisit if it turns out to
  matter in practice.
- 2026-08-12: `GET /google/status`'s `last_synced_at` is computed as the max
  `last_synced_at` across both link tables (`google_links.last_synced_at`) rather than adding
  a dedicated "last sync" column anywhere — the data already exists per-link, no need to
  duplicate it in a new place that could drift out of sync with the links themselves.
- 2026-08-12: Sync tests monkeypatch the thin wrapper functions
  (`app.integrations.google.sync.google_tasks.*`, `...google_calendar.*`) rather than faking
  the full `googleapiclient` discovery/Resource chained-call interface — much simpler to fake a
  handful of plain functions (`ensure_list`, `insert_task`, ...) than to reconstruct
  `service.tasks().insert(...).execute()`-style method chaining, and it's exactly the seam
  `tasks.py`/`calendar.py` exist to provide. 10 tests cover push (new + updates-only-when-
  changed + dropped-tasks-excluded), pull (new-task-from-Google with role/quadrant resolved
  from the notes codec, unchanged-skip), the calendar equivalents, and `sync_all`'s
  degradation path when there's no token yet.

- 2026-08-12: Phase 5 live-verified against real Google APIs (user ran
  `python -m scripts.google_oauth_setup` locally, confirmed real two-way sync). Phase 5
  is fully done. Added `env_sync.py push_google_token <proj>` (mirrors
  `push_broker_files`/`_vm_upload`) since the resulting `google_token.json` is
  gitignored and not covered by `push_env` (which only SCPs .env files); the token JSON
  is self-contained (client_id/secret + refresh_token bundled by `Credentials.to_json()`)
  so copying it to the VM once is sufficient — no need to re-run the interactive OAuth flow
  there.

- 2026-08-13: Phase 6 built (proactive loops + weekly review). Scheduling uses a single
  `scheduler_tick_job` (run_repeating every 60s) rather than four fixed-at-startup
  `run_daily` registrations, because the user wants morning-brief/evening-checkin/
  weekly-review/weekly-planning times live-editable via the web Settings page — the bot
  worker is a separate long-running process from the API, so a `run_daily` time captured
  once at startup would go stale on a settings edit without a restart. The tick re-reads
  `AppSettings` fresh every 60s and fires each behavior once its configured HH:MM has
  passed and it hasn't already fired for that day/week (idempotency via a new `DailyLog`
  row per day, `WeeklyReview.iso_week`'s existing uniqueness, and one new nullable
  `WeekPlan.planning_prompt_sent_at` column) — this collapses idempotency and
  live-editable scheduling into one mechanism. Sunday is hardcoded as the review/planning
  anchor day (not made configurable — SPEC only calls out configurable times).
- 2026-08-13: Fixed a latent bug in `app/ai/agent.py::run_agent_turn`: it always appended
  the new user message before replaying history, so if a proactive job (morning brief,
  evening check-in, Sunday planning prompt) ever pushes the very first message in
  `conversation_messages` as an assistant turn, the replayed `messages` list would start
  with `role: assistant`, which the Anthropic Messages API rejects. Fixed by dropping any
  leading assistant-role messages before the first user-role message when there's no
  conversation summary yet (a summary always yields a user-role message first already).
  Regression test added.
- 2026-08-13: `analyze_week` (§3.3) is a pure function (`app/ai/analysis.py`) taking
  stats/previous-analyses/reflection as plain data, not `db` — unlike the Phase 3 pattern
  where AI functions pull their own context via services. This avoids a circular import
  (`app/services/weekly_review.py` needs `analyze_week`; if `analyze_week` pulled its own
  stats via that same service module, the two would import each other).
  `weekly_review_service.generate_review` is the orchestrator that gathers stats/previous
  reviews and calls `analyze_week`.
- 2026-08-13: Live-verified Phase 6 end to end against the real Anthropic API: seeded a
  role/task via the REST API, called `POST /weeks/{iso}/review/generate` and got back a
  well-formed, schema-valid `WeekAnalysis` (summary/wins/concerns/patterns/suggestions/
  candidates/trend) from a real model call; confirmed `GET`/reflection `PUT` round-trip
  and the new `AppSettings` time fields via `GET /settings`. Confirmed via `tsc`, `eslint`,
  and a production `next build` that the new `/review` page and enabled Settings time
  inputs compile and the route renders (200, no server/compile errors) — did not click
  through the page in an actual browser (no browser tool available this session), so the
  interactive flows (Generate/Regenerate buttons, reflection save, week prev/next, time
  inputs) are unverified beyond static/build checks. Bot-side proactive jobs
  (`scheduler_tick_job`) were verified only via `test_jobs.py`'s simulated-clock unit
  tests, not against the real Telegram bot — that requires running `make dev-bot` with a
  near-future time set in Settings and watching messages actually arrive, left for the
  user to do at their convenience. Reset the local dev DB to a clean migrated state
  afterward. Phase 6 is code-complete and `make check`-green; full live bot verification
  is the one open item before calling it fully done.

- 2026-08-13: Added `/debug tick` (owner-only Telegram command) — added a
  `force: bool` param to `run_tick` that bypasses day-of-week/time-of-day/
  already-sent gating and fires all four proactive behaviors unconditionally
  using real current data. Needed because the weekly review/planning
  behaviors are Sunday-gated, so there was previously no way to exercise
  them without waiting for an actual Sunday. Dispatched via a small
  `DEBUG_ACTIONS` registry in `app/bot/handlers.py` (`/debug <action>`) so
  more debug subcommands can be added later without new command
  registrations. `weekly_review_service.generate_review`'s existing `force`
  param is reused directly rather than adding a second force flag.

- 2026-08-13: Live testing surfaced two real bugs, both fixed:
  1. `_push_proactive_message` (jobs.py) wrote to `conversation_messages`
     *before* the Telegram send — a transient `httpx.ConnectError` during a
     real `/debug tick` test left an orphaned history row for a message
     that never actually reached Telegram, and would have double-sent on
     retry. Fixed by sending first, then recording — a failed send now
     leaves no history row and no "already sent" flag, so the next
     tick/retry sends one clean copy.
  2. `_debug_tick` had no error handling — PTB has no app-wide error
     handler registered, so the exception above surfaced as "No error
     handlers are registered" in the log with zero reply to the user.
     Wrapped in try/except with a reply on failure. A broader fix (a
     registered `Application.add_error_handler`) would help every handler,
     not just this one, but is out of scope here — flagging as a possible
     Phase 7 polish item.
  3. Fixed an unrelated pre-existing test bug found by the same live-testing
     session: `test_compute_week_stats_counts_big_rocks_and_carry_over`
     hardcoded `"2026-W33"` while using real wall-clock task
     created_at/completed_at timestamps — the test silently depended on
     "today" falling inside that week's date range and broke once real time
     moved past it. Fixed to use the actual current ISO week.
