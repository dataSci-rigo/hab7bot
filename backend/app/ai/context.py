"""Shared, compact context-block builders for AI prompts.

Per SPEC §3: "context blocks are compact summaries, never full-table dumps."
"""
from app.models.goal import Goal
from app.models.mission import MissionStatement
from app.models.project import Project
from app.models.role import Role
from app.models.task import Task


def format_mission(mission: MissionStatement) -> str:
    return mission.content.strip() or "(no mission statement written yet)"


def format_roles(roles: list[Role]) -> str:
    if not roles:
        return "(no roles defined yet)"
    return "\n".join(f"- {r.name}" + (f": {r.description}" if r.description else "") for r in roles)


def format_goals(goals: list[Goal], roles_by_id: dict) -> str:
    if not goals:
        return "(no goals yet)"
    lines = []
    for g in goals:
        role_name = roles_by_id.get(g.role_id, "?")
        target = f" (target: {g.target_date})" if g.target_date else ""
        lines.append(f"- [{role_name}] {g.title}{target}")
    return "\n".join(lines)


def format_projects(projects: list[Project], roles_by_id: dict) -> str:
    if not projects:
        return "(no projects yet)"
    lines = []
    for p in projects:
        role_name = roles_by_id.get(p.role_id, "?")
        lines.append(f"- [{role_name}] {p.title} (status: {p.status.value})")
    return "\n".join(lines)


def format_existing_tasks(tasks: list[Task]) -> str:
    if not tasks:
        return "(none yet)"
    return "\n".join(f"- {t.title}" for t in tasks)
