from pydantic import BaseModel, ConfigDict


class AppSettingsUpdate(BaseModel):
    week_start_day: str | None = None
    google_sync_enabled: bool | None = None
    morning_brief_time: str | None = None
    evening_checkin_time: str | None = None
    weekly_review_time: str | None = None
    weekly_planning_time: str | None = None


class AppSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    week_start_day: str
    google_sync_enabled: bool
    morning_brief_time: str
    evening_checkin_time: str
    weekly_review_time: str
    weekly_planning_time: str
