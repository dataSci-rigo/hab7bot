from pydantic import BaseModel, ConfigDict


class AppSettingsUpdate(BaseModel):
    week_start_day: str


class AppSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    week_start_day: str
