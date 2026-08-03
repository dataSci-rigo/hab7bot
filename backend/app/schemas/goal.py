import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class GoalCreate(BaseModel):
    role_id: uuid.UUID
    title: str
    notes: str | None = None
    target_date: date | None = None


class GoalUpdate(BaseModel):
    role_id: uuid.UUID | None = None
    title: str | None = None
    notes: str | None = None
    target_date: date | None = None


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role_id: uuid.UUID
    title: str
    notes: str | None
    target_date: date | None
    created_at: datetime
