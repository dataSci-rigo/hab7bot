import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ProjectOrigin, ProjectStatus


class ProjectCreate(BaseModel):
    role_id: uuid.UUID
    goal_id: uuid.UUID | None = None
    title: str
    notes: str | None = None
    status: ProjectStatus = ProjectStatus.idea
    origin: ProjectOrigin = ProjectOrigin.user


class ProjectUpdate(BaseModel):
    role_id: uuid.UUID | None = None
    goal_id: uuid.UUID | None = None
    title: str | None = None
    notes: str | None = None
    status: ProjectStatus | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role_id: uuid.UUID
    goal_id: uuid.UUID | None
    title: str
    notes: str | None
    status: ProjectStatus
    origin: ProjectOrigin
    created_at: datetime
