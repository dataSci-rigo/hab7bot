import uuid

from sqlalchemy.orm import Session

from app.ai.inbox_triage import triage_inbox
from app.ai.resolve import resolve_project, resolve_role
from app.schemas.inbox_triage import InboxTriageSuggestion
from app.services import projects as projects_service
from app.services import roles as roles_service


def get_inbox_triage_suggestions(db: Session) -> list[InboxTriageSuggestion] | None:
    """Returns None if the AI call failed/degraded (caller should show a retry
    affordance); an empty list only means the inbox itself is empty."""
    result = triage_inbox(db)
    if result is None:
        return None

    roles = roles_service.list_roles(db, active_only=True)
    projects = projects_service.list_projects(db)

    suggestions = []
    for item in result.items:
        role = resolve_role(item.role_name, roles)
        project = resolve_project(item.project_title_match, projects)
        suggestions.append(
            InboxTriageSuggestion(
                task_id=uuid.UUID(item.task_id),
                role_id=role.id if role else None,
                role_name=role.name if role else None,
                quadrant=item.quadrant,
                is_big_rock_candidate=item.is_big_rock_candidate,
                project_id=project.id if project else None,
                project_title=project.title if project else None,
            )
        )
    return suggestions
