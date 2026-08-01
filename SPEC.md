# SPEC.md — "Compass" — 7 Habits Weekly Planner

A self-hosted, single-user weekly planning system based on Stephen Covey's *7 Habits* methodology. Fast capture and conversational planning happen through a **Telegram bot**; structured review, weekly planning, and dashboards happen on a **web app**. An **Anthropic API** integration acts as the planning intelligence: it breaks projects into tasks, suggests projects from long-term goals, and analyzes weekly progress to recommend adjustments.

---

## 1. Core Concepts (Domain Model)

The planner is organized around Covey's framework:

- **Mission Statement** — a single free-text document the user writes and revises. Referenced by the AI in all suggestion/analysis prompts.
- **Role** — a life role the user defines (e.g., "Engineer", "Parent", "Health & Fitness", "Sharpen the Saw"). Everything hangs off roles. 3–8 active roles expected.
- **Goal** — a long-term outcome attached to a Role, with optional target date. (e.g., "Run a half marathon by November").
- **Project** — a multi-step effort that serves a Goal (or directly a Role). Has status: `idea → active → paused → done → abandoned`. Projects can be AI-suggested (flagged `origin=ai`, requires user acceptance) or user-created.
- **Task** — the atomic unit of work. Belongs to a Project or directly to a Role. Fields below.
- **Big Rock** — not a separate entity; a boolean flag on Task (`is_big_rock`). Big rocks are chosen during weekly planning, scheduled *first*, max ~1–3 per role per week (soft limit, warn only).
- **Week Plan** — a container for one ISO week: the selected big rocks, scheduled tasks, and a per-role intention note. Weeks start Monday (configurable to Sunday).
- **Weekly Review** — a record generated at week's end: what was planned vs. done, quadrant distribution, role balance, the AI's analysis, and the user's own reflections.
- **Quadrant** — every task is tagged Q1–Q4 (Urgent/Important matrix):
  - Q1 Urgent + Important (firefighting)
  - Q2 Not Urgent + Important (the target zone — planning, prevention, relationships, growth)
  - Q3 Urgent + Not Important (interruptions)
  - Q4 Not Urgent + Not Important (waste)
  The system's north star metric is **% of completed effort in Q2**.

### Task fields
| Field | Type | Notes |
|---|---|---|
| id | uuid | |
| title | text | required |
| notes | text | optional, markdown |
| role_id | fk | required (directly or inherited via project) |
| project_id | fk nullable | |
| quadrant | enum Q1–Q4 | default Q2; AI suggests on capture |
| is_big_rock | bool | default false |
| status | enum | `inbox → planned → in_progress → done → dropped` |
| scheduled_week | ISO week nullable | null = backlog/inbox |
| scheduled_day | date nullable | optional day-level scheduling |
| estimate_minutes | int nullable | AI-suggested during breakdown |
| actual_minutes | int nullable | optional, user-reported |
| origin | enum | `user`, `ai`, `telegram`, `web` (source of capture) |
| created_at / completed_at | timestamps | completed_at powers analysis |

**Inbox model:** anything captured without a week/project lands in the Inbox (`status=inbox`). Weekly planning is largely the act of triaging inbox → week plan.

---

## 2. Surfaces

### 2.1 Telegram Bot — capture + conversational planning partner
The bot is a **full conversational agent**, not a command menu. The user talks to it naturally; Claude (via the Anthropic API with tool use) interprets and acts on the planner data. Slash commands exist as shortcuts but everything is doable in plain language.

**Behaviors:**
1. **Fast capture.** "add: call the accountant re: Q3 taxes" → task created in Inbox, AI infers role + quadrant, bot confirms in one line with an inline "fix" button (edit role/quadrant/big-rock via inline keyboard).
2. **Conversational planning.** "What should I focus on tomorrow?", "Break down the garage renovation project", "Move the marathon training to next week", "How am I doing on my health goals?" — the agent answers using tools that read/write the database, and asks clarifying questions when needed.
3. **Scheduled touchpoints** (all times configurable, sent proactively):
   - **Morning brief** (default 7:30): today's scheduled tasks, the week's big rocks status, one-line nudge.
   - **Evening check-in** (default 21:00): "What got done today?" — user replies in free text; the agent marks tasks done/moves them and logs a short daily note.
   - **Weekly planning prompt** (default Sunday 17:00): kicks off a guided planning conversation — review last week (AI analysis summary), pick big rocks per role, triage inbox. The conversation produces a draft Week Plan; a link to the web app is included for finishing visually.
   - **Weekly review generation** (default Sunday 16:00, before planning): AI generates the review record so the planning prompt can reference it.
4. **Voice notes:** transcribe voice messages (via a local Whisper model or `faster-whisper`) and treat as text input. *(Phase 2 — see build plan.)*

**Agent architecture:** each Telegram chat turn calls the Anthropic Messages API with:
- System prompt: planner persona + mission statement + roles + current week summary (compact context block, rebuilt per turn).
- Conversation history: last N turns from `conversation_messages` table (rolling window, ~20 turns, with older context summarized).
- Tools (function definitions): `create_task`, `update_task`, `complete_task`, `list_tasks`, `get_week_plan`, `set_big_rocks`, `create_project`, `breakdown_project`, `suggest_projects`, `get_progress_analysis`, `search_tasks`, `add_reflection`.
- Tool-use loop runs server-side until Claude returns a final text reply; reply is sent to Telegram (markdown, kept concise for mobile).

**Safety rails:** destructive actions (delete/drop >1 item, abandoning a project) require an inline-keyboard confirmation before the tool executes.

### 2.2 Web App — review, plan, ingest
Next.js (App Router, TypeScript) frontend against the FastAPI backend. Since it's single-user self-hosted: login is a single shared secret → session cookie (see §5).

**Pages:**
1. **This Week (home)** — kanban-ish weekly board: columns Mon–Sun + Backlog; big rocks pinned at top per role with progress; drag to schedule/reschedule; check off tasks. Quadrant shown as a colored chip.
2. **Inbox** — triage list: assign role/project/quadrant/week in-line; bulk actions; "AI triage" button that pre-fills suggestions for the whole inbox in one call (user accepts/edits).
3. **Roles & Goals** — CRUD for roles, goals, mission statement editor. Per-role view shows goals → projects → recent activity.
4. **Projects** — list + detail. Detail page has the **"Break down with AI"** action: shows proposed milestones/tasks with estimates and quadrants in an editable preview; user accepts all/some; accepted items become real tasks. Also **"Suggest projects"** on the list page: AI proposes 3–5 projects grounded in goals + mission + current portfolio gaps (especially neglected roles / missing Q2 & Sharpen-the-Saw work); each suggestion shows its rationale; accept → creates project as `idea`.
5. **Weekly Review** — the review record for any past week: planned vs. completed, quadrant pie, per-role balance bar, streaks, the AI analysis (see §3.3), and a free-text reflection box (user's own answers to: What went well? What didn't? What will I change?). "Regenerate analysis" button.
6. **Trends** — simple charts across weeks: Q2 %, big-rock completion rate, per-role effort share, tasks captured vs. completed. (Recharts.)
7. **Settings** — Telegram pairing status, check-in times, week start day, Anthropic model choice, data export (JSON dump).

Ingestion on the web = quick-add box available on every page (same AI inference of role/quadrant as Telegram capture) + full task/project forms.

---

## 3. AI Features (Anthropic API)

Client: official `anthropic` Python SDK. Default model **`claude-sonnet-4-6`** (config-swappable via env `ANTHROPIC_MODEL`; docs list it as the balanced production default, with heavier models available if desired). All AI calls live in one module (`app/ai/`) behind typed functions — no raw API calls scattered around. Structured outputs are obtained via **tool use** (define a tool whose input schema is the desired JSON; force it with `tool_choice`), not by parsing free text.

### 3.1 Project breakdown
`breakdown_project(project_id) -> BreakdownProposal`
- Context sent: project title/notes, parent goal, role, mission statement, user's typical week capacity (settings), existing tasks in project.
- Output schema: `{ milestones: [{title, tasks: [{title, estimate_minutes, quadrant, suggested_week_offset}] }], assumptions: [str], questions: [str] }`
- If `questions` is non-empty and confidence is low, the surface (bot or web) asks the user before finalizing.
- Nothing is written to the DB until the user accepts (whole or per-task).

### 3.2 Project suggestions
`suggest_projects() -> [ProjectSuggestion]`
- Context: mission, roles, goals (with target dates), active/idea projects, last 4 weekly reviews (compact), role-balance stats.
- Output per suggestion: `{ title, role, goal_id?, rationale, first_three_tasks, quadrant_profile }`
- Prompted to bias toward: neglected roles, approaching goal deadlines with no active project, absent Q2/renewal ("Sharpen the Saw") work. Max 5, ranked.

### 3.3 Progress analysis (weekly review)
`analyze_week(iso_week) -> WeekAnalysis`
- Context: that week's plan vs. outcomes (computed stats, not raw dumps): big-rock completion, per-quadrant completed effort, per-role effort share vs. stated priorities, carry-over count, capture→completion latency; plus the previous 3 analyses for trend awareness and the user's reflections if written.
- Output schema: `{ summary, wins: [str], concerns: [str], patterns: [str], suggestions: [{change, why, how}], suggested_big_rock_candidates_next_week: [str], q2_percent_trend: str }`
- Tone requirement in prompt: candid, specific, non-preachy; reference actual data; at most 3 suggestions.
- Stored on the WeeklyReview record; regenerable.

### 3.4 Capture-time inference
`infer_task_metadata(text) -> {title, role_id?, quadrant, is_big_rock_candidate, project_match?}` — small/cheap call (can use `claude-haiku-4-5` via `ANTHROPIC_MODEL_FAST`) used on every quick capture. Must degrade gracefully: if the API call fails, the task is still created in Inbox with defaults.

### 3.5 Conversational agent (Telegram)
Described in §2.1. Uses the same tool implementations as the REST layer (shared service functions) so bot and web can't drift.

**Cost controls:** per-day API call budget in settings (default generous); context blocks are compact summaries, never full-table dumps; capture inference uses the fast model.

---

## 4. Architecture

```
┌─────────────┐     long polling      ┌──────────────────────────────┐
│  Telegram    │◄────────────────────►│  bot worker (python-telegram- │
│  (user)      │                      │  bot v21+, asyncio)           │
└─────────────┘                      │   └─ agent loop → Anthropic   │
                                      └──────────────┬───────────────┘
                                                     │ shared service layer
┌─────────────┐   HTTPS (LAN/Tailscale)  ┌───────────▼───────────────┐
│  Next.js     │◄────────────────────────►│  FastAPI (REST, /api/v1)  │
│  web app     │                          │   ├─ services (domain)    │
└─────────────┘                          │   ├─ ai/ (Anthropic SDK)  │
                                          │   └─ APScheduler jobs     │
                                          └───────────┬───────────────┘
                                                      │ SQLAlchemy 2.x
                                                ┌─────▼─────┐
                                                │  SQLite    │  (WAL mode)
                                                └───────────┘
```

- **One repository, two deployable processes** (`api` and `bot`) + the Next.js app; all run via `docker compose` (`api`, `bot`, `web`, optional `caddy` for TLS). A `make dev` target runs them locally without Docker.
- **Bot uses long polling**, not webhooks — no public endpoint needed for self-hosting.
- **SQLite** (file volume-mounted) — right-sized for single user. SQLAlchemy 2.x + Alembic migrations so a later move to Postgres is trivial. WAL mode since two processes touch the DB.
- **Scheduler:** APScheduler inside the bot worker (it owns proactive messaging). Job times read from settings table; jobs are idempotent (e.g., weekly review generation checks it doesn't already exist).
- **Shared service layer:** `app/services/*` contains all domain logic; FastAPI routes and bot agent tools are both thin wrappers over it.

### Tech versions
- Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, `python-telegram-bot` ≥21 (async), APScheduler, `anthropic` SDK (latest), `uv` for dependency management, `ruff` + `pytest`.
- Node 20+, Next.js 15 (App Router), TypeScript, Tailwind, shadcn/ui, Recharts, TanStack Query.

---

## 5. Auth & Security (single-user posture)
- **Web:** login page takes `APP_PASSWORD` (env); success sets an HTTP-only session cookie (signed, `itsdangerous`). All `/api/v1/*` routes require it. CORS locked to the web origin.
- **Telegram:** bot only responds to `TELEGRAM_ALLOWED_USER_ID` (env). All other senders get silence.
- **Secrets:** `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `APP_PASSWORD`, `SESSION_SECRET` via `.env` (never committed; `.env.example` provided).
- Intended deployment: home server / VPS behind Tailscale or Caddy+TLS. No public signup, no multi-tenancy anywhere in the schema (but keep `user_id` off — adding it later is the Postgres-migration moment).

---

## 6. API Surface (REST, /api/v1)
Standard CRUD for roles, goals, projects, tasks, week-plans, reviews, settings — plus:
- `POST /capture` `{text}` → task via inference (§3.4)
- `POST /projects/{id}/breakdown` → BreakdownProposal (no writes)
- `POST /projects/{id}/breakdown/accept` `{selected}` → creates tasks
- `POST /projects/suggestions` → list; `POST /projects/suggestions/accept`
- `GET /weeks/{iso}/plan`, `PUT /weeks/{iso}/big-rocks`
- `POST /weeks/{iso}/review/generate` → runs §3.3
- `GET /stats/trends?weeks=12`
- `GET /export` → full JSON dump

OpenAPI schema is the contract for the frontend; the frontend generates its client types from it.

---

## 7. Non-goals (v1)
- Calendar integration (Google/Outlook) — future phase.
- Mobile app — Telegram + responsive web is the mobile story.
- Multi-user, sharing, teams.
- Time tracking beyond optional manual `actual_minutes`.
- Notifications outside Telegram.

## 8. Success criteria
- Capture from Telegram to Inbox in <3 seconds perceived.
- Full weekly planning doable entirely from Telegram *or* entirely from web.
- Weekly review renders with AI analysis in <20s generation.
- Q2 % and big-rock completion visible as trends after 2+ weeks of data.
- Total infra: one `docker compose up` on a home server.
