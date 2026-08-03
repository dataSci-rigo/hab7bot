from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MissionUpdate(BaseModel):
    content: str


class MissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: str
    updated_at: datetime
