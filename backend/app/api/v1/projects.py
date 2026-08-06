import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.breakdown import breakdown_project as ai_breakdown_project
from app.ai.schemas import BreakdownProposal, ProjectSuggestion
from app.ai.suggestions import suggest_projects as ai_suggest_projects
from app.auth import require_session
from app.db import get_db
from app.models.enums import ProjectStatus
from app.schemas.ai import BreakdownAcceptRequest, SuggestionAcceptRequest
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.task import TaskRead
from app.services import ai_accept as ai_accept_service
from app.services import projects as projects_service

router = APIRouter(prefix="/projects", tags=["projects"], dependencies=[Depends(require_session)])


@router.get("", response_model=list[ProjectRead])
def list_projects(
    role_id: uuid.UUID | None = None,
    goal_id: uuid.UUID | None = None,
    status: ProjectStatus | None = None,
    db: Session = Depends(get_db),
) -> list[ProjectRead]:
    return projects_service.list_projects(db, role_id=role_id, goal_id=goal_id, status=status)


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    return projects_service.create_project(db, data)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> ProjectRead:
    project = projects_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: uuid.UUID, data: ProjectUpdate, db: Session = Depends(get_db)
) -> ProjectRead:
    project = projects_service.update_project(db, project_id, data)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    if not projects_service.delete_project(db, project_id):
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/suggestions", response_model=list[ProjectSuggestion])
def suggest_projects(db: Session = Depends(get_db)) -> list[ProjectSuggestion]:
    result = ai_suggest_projects(db)
    if result is None:
        raise HTTPException(status_code=503, detail="AI is currently unavailable. Try again.")
    return result.suggestions


@router.post("/suggestions/accept", response_model=ProjectRead, status_code=201)
def accept_suggestion(data: SuggestionAcceptRequest, db: Session = Depends(get_db)) -> ProjectRead:
    project = ai_accept_service.accept_project_suggestion(db, data.suggestion)
    if project is None:
        raise HTTPException(status_code=400, detail="Suggested role no longer exists")
    return project


@router.post("/{project_id}/breakdown", response_model=BreakdownProposal)
def breakdown_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> BreakdownProposal:
    if projects_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    result = ai_breakdown_project(db, project_id)
    if result is None:
        raise HTTPException(status_code=503, detail="AI is currently unavailable. Try again.")
    return result


@router.post("/{project_id}/breakdown/accept", response_model=list[TaskRead], status_code=201)
def accept_breakdown(
    project_id: uuid.UUID, data: BreakdownAcceptRequest, db: Session = Depends(get_db)
) -> list[TaskRead]:
    project = projects_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ai_accept_service.accept_breakdown_tasks(db, project_id, project.role_id, data.selected)
