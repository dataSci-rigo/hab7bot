import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import Quadrant, TaskOrigin, TaskStatus


class TaskCreate(BaseModel):
    title: str
    notes: str | None = None
    role_id: uuid.UUID
    project_id: uuid.UUID | None = None
    quadrant: Quadrant = Quadrant.Q2
    is_big_rock: bool = False
    status: TaskStatus = TaskStatus.inbox
    scheduled_week: str | None = None
    scheduled_day: date | None = None
    estimate_minutes: int | None = None
    origin: TaskOrigin = TaskOrigin.user


class TaskUpdate(BaseModel):
    title: str | None = None
    notes: str | None = None
    role_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    quadrant: Quadrant | None = None
    is_big_rock: bool | None = None
    status: TaskStatus | None = None
    scheduled_week: str | None = None
    scheduled_day: date | None = None
    estimate_minutes: int | None = None
    actual_minutes: int | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    notes: str | None
    role_id: uuid.UUID
    project_id: uuid.UUID | None
    quadrant: Quadrant
    is_big_rock: bool
    status: TaskStatus
    scheduled_week: str | None
    scheduled_day: date | None
    estimate_minutes: int | None
    actual_minutes: int | None
    origin: TaskOrigin
    created_at: datetime
    completed_at: datetime | None
