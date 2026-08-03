from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.goal import Goal
    from app.models.project import Project
    from app.models.task import Task


class Role(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str | None] = mapped_column(String, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    goals: Mapped[list["Goal"]] = relationship(back_populates="role", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="role", cascade="all, delete-orphan")
