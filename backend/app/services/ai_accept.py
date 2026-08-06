"""Turns accepted AI proposals into real rows. Nothing in app/ai/ ever
writes to the DB — this is the one place breakdown/suggestion acceptance
happens, shared by the web API and (later) the Telegram bot."""
import uuid

from sqlalchemy.orm import Session

from app.ai.schemas import BreakdownTask, ProjectSuggestion
from app.models.enums import ProjectOrigin, ProjectStatus, TaskOrigin, TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.services.goals import list_goals
from app.services.iso_week import current_iso_week_plus
from app.services.roles import list_roles


def accept_breakdown_tasks(
    db: Session, project_id: uuid.UUID, role_id: uuid.UUID, selected: list[BreakdownTask]
) -> list[Task]:
    tasks = [
        Task(
            title=item.title,
            role_id=role_id,
            project_id=project_id,
            quadrant=item.quadrant,
            estimate_minutes=item.estimate_minutes,
            scheduled_week=current_iso_week_plus(item.suggested_week_offset),
            status=TaskStatus.planned,
            origin=TaskOrigin.ai,
        )
        for item in selected
    ]
    db.add_all(tasks)
    db.commit()
    for task in tasks:
        db.refresh(task)
    return tasks


def accept_project_suggestion(db: Session, suggestion: ProjectSuggestion) -> Project | None:
    roles_by_name = {r.name.strip().lower(): r for r in list_roles(db, active_only=True)}
    role = roles_by_name.get(suggestion.role_name.strip().lower())
    if role is None:
        return None

    goal_id = None
    if suggestion.goal_title:
        goals_by_title = {g.title.strip().lower(): g for g in list_goals(db, role_id=role.id)}
        goal = goals_by_title.get(suggestion.goal_title.strip().lower())
        if goal is not None:
            goal_id = goal.id

    project = Project(
        title=suggestion.title,
        role_id=role.id,
        goal_id=goal_id,
        notes=suggestion.rationale,
        status=ProjectStatus.idea,
        origin=ProjectOrigin.ai,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
