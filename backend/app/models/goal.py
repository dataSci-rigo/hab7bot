import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.role import Role


class Goal(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "goals"

    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"))
    title: Mapped[str] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(String, default=None)
    target_date: Mapped[date | None] = mapped_column(Date, default=None)

    role: Mapped["Role"] = relationship(back_populates="goals")
    projects: Mapped[list["Project"]] = relationship(back_populates="goal")
