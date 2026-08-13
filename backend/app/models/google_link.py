import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import UUIDPKMixin


class GoogleTaskLink(UUIDPKMixin, Base):
    """Links a Task to a Google Task for two-way sync — see SPEC §5."""

    __tablename__ = "google_task_links"

    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"), unique=True)
    google_task_id: Mapped[str] = mapped_column(String)
    google_list_id: Mapped[str] = mapped_column(String)
    google_updated_at: Mapped[str | None] = mapped_column(String, default=None)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)


class GoogleCalendarEventLink(UUIDPKMixin, Base):
    """Links a Task to a Google Calendar event for two-way sync — see SPEC §5."""

    __tablename__ = "google_calendar_event_links"

    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"), unique=True)
    google_event_id: Mapped[str] = mapped_column(String)
    google_calendar_id: Mapped[str] = mapped_column(String)
    google_updated_at: Mapped[str | None] = mapped_column(String, default=None)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
