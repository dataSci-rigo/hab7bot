import uuid

from pydantic import BaseModel

from app.models.enums import Quadrant


class InboxTriageSuggestion(BaseModel):
    task_id: uuid.UUID
    role_id: uuid.UUID | None
    role_name: str | None
    quadrant: Quadrant
    is_big_rock_candidate: bool
    project_id: uuid.UUID | None
    project_title: str | None
