import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import ProjectOrigin, ProjectStatus
from app.models.mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.goal import Goal
    from app.models.role import Role
    from app.models.task import Task


class Project(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "projects"

    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"))
    goal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("goals.id"), default=None)
    title: Mapped[str] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(String, default=None)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, native_enum=False), default=ProjectStatus.idea
    )
    origin: Mapped[ProjectOrigin] = mapped_column(
        Enum(ProjectOrigin, native_enum=False), default=ProjectOrigin.user
    )

    role: Mapped["Role"] = relationship(back_populates="projects")
    goal: Mapped["Goal | None"] = relationship(back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship(back_populates="project")
