from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import UUIDPKMixin


class AppSettings(UUIDPKMixin, Base):
    """Singleton — the app only ever reads/writes the single most recent row.

    `week_start_day` (Phase 2), `google_sync_enabled` (Phase 5), and the
    four *_time fields (Phase 6, HH:MM 24h strings) are functional; model
    choice and Telegram pairing settings are added when their owning phase
    (7) lands.
    """

    __tablename__ = "settings"

    week_start_day: Mapped[str] = mapped_column(String(10), default="monday")
    google_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    morning_brief_time: Mapped[str] = mapped_column(String(5), default="07:30")
    evening_checkin_time: Mapped[str] = mapped_column(String(5), default="21:00")
    weekly_review_time: Mapped[str] = mapped_column(String(5), default="16:00")
    weekly_planning_time: Mapped[str] = mapped_column(String(5), default="17:00")
