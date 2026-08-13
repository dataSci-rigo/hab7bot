import uuid
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import TaskStatus
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, data: TaskCreate) -> Task:
    task = Task(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: uuid.UUID) -> Task | None:
    return db.get(Task, task_id)


def list_tasks(
    db: Session,
    role_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    status: TaskStatus | None = None,
    scheduled_week: str | None = None,
    scheduled_day: date | None = None,
) -> list[Task]:
    stmt = select(Task)
    if role_id is not None:
        stmt = stmt.where(Task.role_id == role_id)
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    if status is not None:
        stmt = stmt.where(Task.status == status)
    if scheduled_week is not None:
        stmt = stmt.where(Task.scheduled_week == scheduled_week)
    if scheduled_day is not None:
        stmt = stmt.where(Task.scheduled_day == scheduled_day)
    return list(db.scalars(stmt.order_by(Task.created_at)))


def search_tasks(db: Session, query: str, limit: int = 20) -> list[Task]:
    stmt = (
        select(Task)
        .where(Task.title.ilike(f"%{query}%"))
        .order_by(Task.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def update_task(db: Session, task_id: uuid.UUID, data: TaskUpdate) -> Task | None:
    task = get_task(db, task_id)
    if task is None:
        return None
    updates = data.model_dump(exclude_unset=True)

    # Assigning a project or week is what "triaging out of the inbox" means
    # per SPEC's Inbox model — advance status so the task leaves the inbox
    # view, regardless of which surface (web, bot) made the change. Skipped
    # if the caller already set status explicitly in this same update.
    leaves_inbox = updates.get("project_id") or updates.get("scheduled_week")
    if task.status == TaskStatus.inbox and leaves_inbox and "status" not in updates:
        updates["status"] = TaskStatus.planned

    for field, value in updates.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def complete_task(db: Session, task_id: uuid.UUID) -> Task | None:
    task = get_task(db, task_id)
    if task is None:
        return None
    task.status = TaskStatus.done
    task.completed_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(task)
    return task


def uncomplete_task(db: Session, task_id: uuid.UUID) -> Task | None:
    task = get_task(db, task_id)
    if task is None:
        return None
    task.status = TaskStatus.planned
    task.completed_at = None
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: uuid.UUID) -> bool:
    task = get_task(db, task_id)
    if task is None:
        return False
    db.delete(task)
    db.commit()
    return True
