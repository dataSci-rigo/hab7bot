"""Anthropic tool definitions for the conversational agent (SPEC §2.1).

Offered together with tool_choice="auto" (see app/ai/agent.py) — the model
picks zero or more of these per turn, unlike the forced single-tool schemas
in definitions.py. Dispatch lives in app/ai/agent_tools.py.
"""

QUADRANT_ENUM = ["Q1", "Q2", "Q3", "Q4"]
TASK_STATUS_ENUM = ["inbox", "planned", "in_progress", "done", "dropped"]
PROJECT_STATUS_ENUM = ["idea", "active", "paused", "done"]  # abandoned: see abandon_project

AGENT_TOOLS = [
    {
        "name": "create_task",
        "description": "Create a new task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "role_name": {"type": "string", "description": "Must match an existing role."},
                "project_title": {"type": "string"},
                "quadrant": {"type": "string", "enum": QUADRANT_ENUM, "default": "Q2"},
                "is_big_rock": {"type": "boolean", "default": False},
                "scheduled_week": {
                    "type": "string",
                    "description": "ISO week, e.g. '2026-W32'. Omit to leave unscheduled.",
                },
                "scheduled_day": {"type": "string", "description": "ISO date, e.g. '2026-08-10'."},
                "estimate_minutes": {"type": "integer"},
            },
            "required": ["title", "role_name"],
        },
    },
    {
        "name": "list_tasks",
        "description": "List tasks, optionally filtered.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role_name": {"type": "string"},
                "status": {"type": "string", "enum": TASK_STATUS_ENUM},
                "scheduled_week": {"type": "string"},
            },
        },
    },
    {
        "name": "search_tasks",
        "description": "Search tasks by title substring — use this to find a task's id "
        "before updating/completing/dropping it when you don't already have the id.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "update_task",
        "description": "Edit an existing task's fields. Use complete_task/drop_task for "
        "status changes to done/dropped instead.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "title": {"type": "string"},
                "role_name": {"type": "string"},
                "project_title": {"type": "string"},
                "quadrant": {"type": "string", "enum": QUADRANT_ENUM},
                "is_big_rock": {"type": "boolean"},
                "scheduled_week": {"type": "string"},
                "scheduled_day": {"type": "string"},
                "estimate_minutes": {"type": "integer"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "complete_task",
        "description": "Mark a task done.",
        "input_schema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
    },
    {
        "name": "drop_task",
        "description": "Drop/abandon a task (destructive — requires user confirmation before "
        "it actually runs).",
        "input_schema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
    },
    {
        "name": "get_week_plan",
        "description": "Get the plan for a week: big rocks, scheduled tasks, role intentions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "iso_week": {
                    "type": "string",
                    "description": "ISO week e.g. '2026-W32'. Omit for the current week.",
                }
            },
        },
    },
    {
        "name": "set_big_rocks",
        "description": "Pin one or more tasks as this week's big rocks (additive).",
        "input_schema": {
            "type": "object",
            "properties": {"task_ids": {"type": "array", "items": {"type": "string"}}},
            "required": ["task_ids"],
        },
    },
    {
        "name": "list_projects",
        "description": "List projects, optionally filtered — use this to find a project's "
        "id (e.g. before calling breakdown_project/update_project/abandon_project) or to "
        "check whether a project with a given name already exists before creating one.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role_name": {"type": "string"},
                "status": {"type": "string", "enum": [*PROJECT_STATUS_ENUM, "abandoned"]},
            },
        },
    },
    {
        "name": "create_project",
        "description": "Create a new project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "role_name": {"type": "string"},
                "goal_title": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["title", "role_name"],
        },
    },
    {
        "name": "update_project",
        "description": "Edit a project's title/notes/status (idea/active/paused/done). "
        "Use abandon_project to abandon it instead.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "title": {"type": "string"},
                "notes": {"type": "string"},
                "status": {"type": "string", "enum": PROJECT_STATUS_ENUM},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "abandon_project",
        "description": "Abandon a project (destructive — requires user confirmation before "
        "it actually runs).",
        "input_schema": {
            "type": "object",
            "properties": {"project_id": {"type": "string"}},
            "required": ["project_id"],
        },
    },
    {
        "name": "breakdown_project",
        "description": "Ask the AI to propose a milestone/task breakdown for a project. "
        "Nothing is created until you call accept_breakdown_tasks with the tasks the user "
        "wants.",
        "input_schema": {
            "type": "object",
            "properties": {"project_id": {"type": "string"}},
            "required": ["project_id"],
        },
    },
    {
        "name": "accept_breakdown_tasks",
        "description": "Create real tasks from a breakdown_project proposal — pass exactly "
        "the milestone tasks the user wants to keep.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "estimate_minutes": {"type": "integer"},
                            "quadrant": {"type": "string", "enum": QUADRANT_ENUM},
                            "suggested_week_offset": {"type": "integer"},
                        },
                        "required": ["title"],
                    },
                },
            },
            "required": ["project_id", "tasks"],
        },
    },
    {
        "name": "suggest_projects",
        "description": "Ask the AI to suggest up to 5 new projects grounded in the mission/"
        "roles/goals. Nothing is created until you call accept_project_suggestion.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "accept_project_suggestion",
        "description": "Create a real project from one suggest_projects result — pass the "
        "exact suggestion fields back.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "role_name": {"type": "string"},
                "goal_title": {"type": "string"},
                "rationale": {"type": "string"},
                "first_three_tasks": {"type": "array", "items": {"type": "string"}},
                "quadrant_profile": {"type": "string"},
            },
            "required": [
                "title",
                "role_name",
                "rationale",
                "first_three_tasks",
                "quadrant_profile",
            ],
        },
    },
    {
        "name": "get_progress_analysis",
        "description": "Read an already-generated weekly review (stats + AI analysis). "
        "Does NOT generate one — if none exists yet for the requested week, say so; "
        "reviews are generated automatically at week's end or from the web Regenerate button.",
        "input_schema": {
            "type": "object",
            "properties": {
                "iso_week": {
                    "type": "string",
                    "description": "ISO week e.g. '2026-W32'. Omit for the current week.",
                }
            },
        },
    },
    {
        "name": "add_reflection",
        "description": "Save the user's free-text reflection on a week, e.g. from the guided "
        "Sunday planning conversation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "iso_week": {
                    "type": "string",
                    "description": "ISO week e.g. '2026-W32'. Omit for the current week.",
                },
                "reflection": {"type": "string"},
            },
            "required": ["reflection"],
        },
    },
    {
        "name": "log_daily_note",
        "description": "Log a short note about today, e.g. from the evening check-in reply.",
        "input_schema": {
            "type": "object",
            "properties": {"note": {"type": "string"}},
            "required": ["note"],
        },
    },
]
