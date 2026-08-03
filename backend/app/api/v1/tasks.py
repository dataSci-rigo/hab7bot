import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_session
from app.db import get_db
from app.models.enums import TaskStatus
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services import tasks as tasks_service

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(require_session)])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    role_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    status: TaskStatus | None = None,
    scheduled_week: str | None = None,
    db: Session = Depends(get_db),
) -> list[TaskRead]:
    return tasks_service.list_tasks(
        db, role_id=role_id, project_id=project_id, status=status, scheduled_week=scheduled_week
    )


@router.post("", response_model=TaskRead, status_code=201)
def create_task(data: TaskCreate, db: Session = Depends(get_db)) -> TaskRead:
    return tasks_service.create_task(db, data)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> TaskRead:
    task = tasks_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskRead)
def update_task(task_id: uuid.UUID, data: TaskUpdate, db: Session = Depends(get_db)) -> TaskRead:
    task = tasks_service.update_task(db, task_id, data)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/complete", response_model=TaskRead)
def complete_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> TaskRead:
    task = tasks_service.complete_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/uncomplete", response_model=TaskRead)
def uncomplete_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> TaskRead:
    task = tasks_service.uncomplete_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    if not tasks_service.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
