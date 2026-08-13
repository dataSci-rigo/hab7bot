from datetime import date

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin


class DailyLog(UUIDPKMixin, CreatedAtMixin, Base):
    """One row per calendar day — tracks whether the morning brief / evening
    check-in have already fired today (scheduler idempotency) and holds the
    short daily note logged from the evening check-in reply.
    """

    __tablename__ = "daily_logs"

    log_date: Mapped[date] = mapped_column(Date, unique=True)
    morning_brief_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    evening_checkin_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str | None] = mapped_column(String, default=None)
