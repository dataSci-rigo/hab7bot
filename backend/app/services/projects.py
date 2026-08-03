import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ProjectStatus
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, data: ProjectCreate) -> Project:
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: uuid.UUID) -> Project | None:
    return db.get(Project, project_id)


def list_projects(
    db: Session,
    role_id: uuid.UUID | None = None,
    goal_id: uuid.UUID | None = None,
    status: ProjectStatus | None = None,
) -> list[Project]:
    stmt = select(Project)
    if role_id is not None:
        stmt = stmt.where(Project.role_id == role_id)
    if goal_id is not None:
        stmt = stmt.where(Project.goal_id == goal_id)
    if status is not None:
        stmt = stmt.where(Project.status == status)
    return list(db.scalars(stmt.order_by(Project.created_at)))


def update_project(db: Session, project_id: uuid.UUID, data: ProjectUpdate) -> Project | None:
    project = get_project(db, project_id)
    if project is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: uuid.UUID) -> bool:
    project = get_project(db, project_id)
    if project is None:
        return False
    db.delete(project)
    db.commit()
    return True
