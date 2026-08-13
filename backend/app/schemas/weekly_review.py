import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WeeklyReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    iso_week: str
    stats: dict | None
    ai_analysis: dict | None
    reflection: str | None
    created_at: datetime


class ReflectionUpdate(BaseModel):
    reflection: str
