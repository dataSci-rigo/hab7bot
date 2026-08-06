from sqlalchemy.orm import Session

from app.ai.capture import infer_task_metadata
from app.ai.resolve import resolve_project, resolve_role
from app.models.enums import Quadrant, TaskOrigin, TaskStatus
from app.models.task import Task
from app.services import projects as projects_service
from app.services import roles as roles_service


def capture_task(db: Session, text: str, origin: TaskOrigin = TaskOrigin.web) -> Task:
    """§3.4 capture. Must degrade gracefully: the task is always created,
    with AI-inferred fields where available and safe defaults otherwise."""
    title = text.strip()[:300] or "(untitled)"
    role_id = None
    quadrant = Quadrant.Q2
    is_big_rock = False
    project_id = None

    inference = infer_task_metadata(db, text)
    if inference is not None:
        title = inference.title.strip()[:300] or title
        quadrant = inference.quadrant
        is_big_rock = inference.is_big_rock_candidate

        roles = roles_service.list_roles(db, active_only=True)
        role = resolve_role(inference.role_name, roles)
        if role is not None:
            role_id = role.id

        if inference.project_title_match:
            projects = projects_service.list_projects(db)
            project = resolve_project(inference.project_title_match, projects)
            if project is not None:
                project_id = project.id
                role_id = project.role_id

    if role_id is None:
        fallback_roles = roles_service.list_roles(db, active_only=True)
        if fallback_roles:
            role_id = fallback_roles[0].id

    task = Task(
        title=title,
        role_id=role_id,
        project_id=project_id,
        quadrant=quadrant,
        is_big_rock=is_big_rock,
        status=TaskStatus.inbox,
        origin=origin,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
