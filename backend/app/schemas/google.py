from datetime import datetime

from pydantic import BaseModel


class GoogleStatus(BaseModel):
    connected: bool
    last_synced_at: datetime | None = None


class GoogleSyncResult(BaseModel):
    ok: bool
    reason: str | None = None
    tasks: dict[str, int] | None = None
    calendar: dict[str, int] | None = None
