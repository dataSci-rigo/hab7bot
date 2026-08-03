from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import UUIDPKMixin


class AppSettings(UUIDPKMixin, Base):
    """Singleton — the app only ever reads/writes the single most recent row.

    Only `week_start_day` is functional as of Phase 2; other planner settings
    (check-in times, model choice, Telegram pairing) are added when their
    owning phase (4/5/6) lands.
    """

    __tablename__ = "settings"

    week_start_day: Mapped[str] = mapped_column(String(10), default="monday")
