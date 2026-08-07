"""Tool definitions + dispatch for the Telegram conversational agent
(SPEC §2.1). Unlike app/ai/schemas.py (forced single-tool structured
extraction), these tools are offered together with `tool_choice: auto` so
the model can chain several calls — e.g. search_tasks to find an id, then
update_task with it — within one turn.

Nothing here writes straight to the DB without going through the same
services/ functions the REST API uses.
"""
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.ai.breakdown import breakdown_project as ai_breakdown_project
from app.ai.resolve import resolve_project, resolve_role
from app.ai.schemas import BreakdownTask, ProjectSuggestion
from app.ai.suggestions import suggest_projects as ai_suggest_projects
from app.models.enums import ProjectStatus, Quadrant, TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import ai_accept as ai_accept_service
from app.services import goals as goals_service
from app.services import projects as projects_service
from app.services import roles as roles_service
from app.services import tasks as tasks_service
from app.services import week_plans as week_plans_service
from app.services.iso_week import current_iso_week_plus

# Tool names whose *execution* the bot must gate behind an inline-keyboard
# confirmation before calling dispatch_tool — SPEC §2.1 "destructive-action
# confirmations". The agent loop checks membership here, not this module.
CONFIRMATION_REQUIRED = {"drop_task", "abandon_project"}


class ToolError(Exception):
    """Raised for bad tool input (unknown id/name) — turned into a text
    tool_result so the model can recover conversationally instead of the
    whole turn erroring out."""


def _role_lookup(db: Session) -> tuple[list, dict]:
    roles = roles_service.list_roles(db, active_only=True)
    by_id = {r.id: r.name for r in roles}
    return roles, by_id


def _project_lookup(db: Session) -> tuple[list, dict]:
    projects = projects_service.list_projects(db)
    by_id = {p.id: p.title for p in projects}
    return projects, by_id


def _task_brief(task: Task, roles_by_id: dict, projects_by_id: dict) -> dict[str, Any]:
    return {
        "id": str(task.id),
        "title": task.title,
        "role": roles_by_id.get(task.role_id, "?"),
        "project": projects_by_id.get(task.project_id) if task.project_id else None,
        "quadrant": task.quadrant.value,
        "is_big_rock": task.is_big_rock,
        "status": task.status.value,
        "scheduled_week": task.scheduled_week,
        "scheduled_day": task.scheduled_day.isoformat() if task.scheduled_day else None,
        "estimate_minutes": task.estimate_minutes,
    }


def _project_brief(project: Project, roles_by_id: dict) -> dict[str, Any]:
    return {
        "id": str(project.id),
        "title": project.title,
        "role": roles_by_id.get(project.role_id, "?"),
        "status": project.status.value,
        "notes": project.notes,
    }


def _require_task(db: Session, task_id: str) -> Task:
    task = tasks_service.get_task(db, uuid.UUID(task_id))
    if task is None:
        raise ToolError(f"No task with id {task_id}")
    return task


def _require_project(db: Session, project_id: str) -> Project:
    project = projects_service.get_project(db, uuid.UUID(project_id))
    if project is None:
        raise ToolError(f"No project with id {project_id}")
    return project


def _require_role(db: Session, role_name: str):
    roles, _ = _role_lookup(db)
    role = resolve_role(role_name, roles)
    if role is None:
        raise ToolError(f"No role named '{role_name}'. Existing roles: {[r.name for r in roles]}")
    return role


# ── tool implementations ────────────────────────────────────────────────────


def _create_task(db: Session, args: dict) -> dict:
    role = _require_role(db, args["role_name"])
    project_id = None
    if args.get("project_title"):
        projects, _ = _project_lookup(db)
        project = resolve_project(args["project_title"], projects)
        project_id = project.id if project else None

    task = tasks_service.create_task(
        db,
        TaskCreate(
            title=args["title"],
            role_id=role.id,
            project_id=project_id,
            quadrant=Quadrant(args.get("quadrant", "Q2")),
            is_big_rock=args.get("is_big_rock", False),
            status=TaskStatus.planned,
            scheduled_week=args.get("scheduled_week"),
            scheduled_day=args.get("scheduled_day"),
            estimate_minutes=args.get("estimate_minutes"),
        ),
    )
    roles, roles_by_id = _role_lookup(db)
    _, projects_by_id = _project_lookup(db)
    return _task_brief(task, roles_by_id, projects_by_id)


def _list_tasks(db: Session, args: dict) -> dict:
    role_id = None
    if args.get("role_name"):
        role = _require_role(db, args["role_name"])
        role_id = role.id
    status = TaskStatus(args["status"]) if args.get("status") else None
    tasks = tasks_service.list_tasks(
        db, role_id=role_id, status=status, scheduled_week=args.get("scheduled_week")
    )
    _, roles_by_id = _role_lookup(db)
    _, projects_by_id = _project_lookup(db)
    return {"tasks": [_task_brief(t, roles_by_id, projects_by_id) for t in tasks]}


def _search_tasks(db: Session, args: dict) -> dict:
    tasks = tasks_service.search_tasks(db, args["query"])
    _, roles_by_id = _role_lookup(db)
    _, projects_by_id = _project_lookup(db)
    return {"tasks": [_task_brief(t, roles_by_id, projects_by_id) for t in tasks]}


def _update_task(db: Session, args: dict) -> dict:
    task = _require_task(db, args["task_id"])
    update = TaskUpdate()
    if "title" in args:
        update.title = args["title"]
    if args.get("role_name"):
        update.role_id = _require_role(db, args["role_name"]).id
    if args.get("project_title"):
        projects, _ = _project_lookup(db)
        project = resolve_project(args["project_title"], projects)
        if project is None:
            raise ToolError(f"No project titled '{args['project_title']}'")
        update.project_id = project.id
    if "quadrant" in args:
        update.quadrant = Quadrant(args["quadrant"])
    if "is_big_rock" in args:
        update.is_big_rock = args["is_big_rock"]
    if "scheduled_week" in args:
        update.scheduled_week = args["scheduled_week"]
    if "scheduled_day" in args:
        update.scheduled_day = args["scheduled_day"]
    if "estimate_minutes" in args:
        update.estimate_minutes = args["estimate_minutes"]

    updated = tasks_service.update_task(db, task.id, update)
    roles, roles_by_id = _role_lookup(db)
    _, projects_by_id = _project_lookup(db)
    return _task_brief(updated, roles_by_id, projects_by_id)


def _complete_task(db: Session, args: dict) -> dict:
    task = _require_task(db, args["task_id"])
    updated = tasks_service.complete_task(db, task.id)
    roles, roles_by_id = _role_lookup(db)
    _, projects_by_id = _project_lookup(db)
    return _task_brief(updated, roles_by_id, projects_by_id)


def _drop_task(db: Session, args: dict) -> dict:
    task = _require_task(db, args["task_id"])
    updated = tasks_service.update_task(db, task.id, TaskUpdate(status=TaskStatus.dropped))
    roles, roles_by_id = _role_lookup(db)
    _, projects_by_id = _project_lookup(db)
    return _task_brief(updated, roles_by_id, projects_by_id)


def _get_week_plan(db: Session, args: dict) -> dict:
    iso_week = args.get("iso_week") or current_iso_week_plus(0)
    view = week_plans_service.get_week_plan_view(db, iso_week)
    _, roles_by_id = _role_lookup(db)
    _, projects_by_id = _project_lookup(db)
    return {
        "iso_week": view["iso_week"],
        "big_rocks": [_task_brief(t, roles_by_id, projects_by_id) for t in view["big_rocks"]],
        "scheduled_tasks": [
            _task_brief(t, roles_by_id, projects_by_id) for t in view["scheduled_tasks"]
        ],
        "role_intentions": [
            {"role": roles_by_id.get(ri.role_id, "?"), "note": ri.note}
            for ri in view["role_intentions"]
        ],
    }


def _set_big_rocks(db: Session, args: dict) -> dict:
    updated = []
    roles, roles_by_id = _role_lookup(db)
    _, projects_by_id = _project_lookup(db)
    for task_id in args["task_ids"]:
        task = _require_task(db, task_id)
        updated.append(tasks_service.update_task(db, task.id, TaskUpdate(is_big_rock=True)))
    return {"updated": [_task_brief(t, roles_by_id, projects_by_id) for t in updated]}


def _create_project(db: Session, args: dict) -> dict:
    role = _require_role(db, args["role_name"])
    goal_id = None
    if args.get("goal_title"):
        goals = goals_service.list_goals(db, role_id=role.id)
        match = next(
            (g for g in goals if g.title.strip().lower() == args["goal_title"].strip().lower()),
            None,
        )
        goal_id = match.id if match else None
    project = projects_service.create_project(
        db,
        ProjectCreate(
            title=args["title"], role_id=role.id, goal_id=goal_id, notes=args.get("notes")
        ),
    )
    _, roles_by_id = _role_lookup(db)
    return _project_brief(project, roles_by_id)


def _update_project(db: Session, args: dict) -> dict:
    project = _require_project(db, args["project_id"])
    update = ProjectUpdate()
    if "title" in args:
        update.title = args["title"]
    if "notes" in args:
        update.notes = args["notes"]
    if args.get("status"):
        status = ProjectStatus(args["status"])
        if status == ProjectStatus.abandoned:
            raise ToolError("Use abandon_project to abandon a project (requires confirmation).")
        update.status = status
    updated = projects_service.update_project(db, project.id, update)
    _, roles_by_id = _role_lookup(db)
    return _project_brief(updated, roles_by_id)


def _abandon_project(db: Session, args: dict) -> dict:
    project = _require_project(db, args["project_id"])
    updated = projects_service.update_project(
        db, project.id, ProjectUpdate(status=ProjectStatus.abandoned)
    )
    _, roles_by_id = _role_lookup(db)
    return _project_brief(updated, roles_by_id)


def _breakdown_project(db: Session, args: dict) -> dict:
    project = _require_project(db, args["project_id"])
    proposal = ai_breakdown_project(db, project.id)
    if proposal is None:
        raise ToolError("AI is currently unavailable for breakdowns. Try again shortly.")
    return proposal.model_dump()


def _accept_breakdown_tasks(db: Session, args: dict) -> dict:
    project = _require_project(db, args["project_id"])
    selected = [BreakdownTask.model_validate(t) for t in args["tasks"]]
    created = ai_accept_service.accept_breakdown_tasks(db, project.id, project.role_id, selected)
    _, roles_by_id = _role_lookup(db)
    _, projects_by_id = _project_lookup(db)
    return {"created": [_task_brief(t, roles_by_id, projects_by_id) for t in created]}


def _suggest_projects(db: Session, _args: dict) -> dict:
    result = ai_suggest_projects(db)
    if result is None:
        raise ToolError("AI is currently unavailable for suggestions. Try again shortly.")
    return {"suggestions": [s.model_dump() for s in result.suggestions]}


def _accept_project_suggestion(db: Session, args: dict) -> dict:
    suggestion = ProjectSuggestion.model_validate(args)
    project = ai_accept_service.accept_project_suggestion(db, suggestion)
    if project is None:
        raise ToolError(f"No role named '{suggestion.role_name}'.")
    _, roles_by_id = _role_lookup(db)
    return _project_brief(project, roles_by_id)


_DISPATCH = {
    "create_task": _create_task,
    "list_tasks": _list_tasks,
    "search_tasks": _search_tasks,
    "update_task": _update_task,
    "complete_task": _complete_task,
    "drop_task": _drop_task,
    "get_week_plan": _get_week_plan,
    "set_big_rocks": _set_big_rocks,
    "create_project": _create_project,
    "update_project": _update_project,
    "abandon_project": _abandon_project,
    "breakdown_project": _breakdown_project,
    "accept_breakdown_tasks": _accept_breakdown_tasks,
    "suggest_projects": _suggest_projects,
    "accept_project_suggestion": _accept_project_suggestion,
}


def dispatch_tool(db: Session, name: str, args: dict) -> dict:
    handler = _DISPATCH.get(name)
    if handler is None:
        raise ToolError(f"Unknown tool '{name}'")
    return handler(db, args)
