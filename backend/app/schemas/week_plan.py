import uuid

from pydantic import BaseModel

from app.schemas.task import TaskRead


class RoleIntentionRead(BaseModel):
    role_id: uuid.UUID
    note: str


class RoleIntentionSet(BaseModel):
    note: str


class WeekPlanRead(BaseModel):
    iso_week: str
    big_rocks: list[TaskRead]
    scheduled_tasks: list[TaskRead]
    role_intentions: list[RoleIntentionRead]
