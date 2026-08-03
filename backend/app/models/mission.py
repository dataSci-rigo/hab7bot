from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import UUIDPKMixin


class MissionStatement(UUIDPKMixin, Base):
    """Singleton — the app only ever reads/writes the single most recent row."""

    __tablename__ = "mission_statement"

    content: Mapped[str] = mapped_column(String, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
