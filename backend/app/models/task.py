import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import Quadrant, TaskOrigin, TaskStatus
from app.models.mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.role import Role


class Task(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(String, default=None)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"))
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"), default=None)

    quadrant: Mapped[Quadrant] = mapped_column(
        Enum(Quadrant, native_enum=False), default=Quadrant.Q2
    )
    is_big_rock: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False), default=TaskStatus.inbox
    )

    # ISO week, e.g. "2026-W32"
    scheduled_week: Mapped[str | None] = mapped_column(String(8), default=None)
    scheduled_day: Mapped[date | None] = mapped_column(Date, default=None)

    estimate_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    actual_minutes: Mapped[int | None] = mapped_column(Integer, default=None)

    origin: Mapped[TaskOrigin] = mapped_column(
        Enum(TaskOrigin, native_enum=False), default=TaskOrigin.user
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    # Python-side default/onupdate (not server_default/server_onupdate) — see
    # the ConversationMessage.created_at fix in Phase 4 for why: SQLite's
    # CURRENT_TIMESTAMP only has 1-second resolution, and Google sync's
    # last-write-wins conflict resolution needs a reliable ordering.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    role: Mapped["Role"] = relationship(back_populates="tasks")
    project: Mapped["Project | None"] = relationship(back_populates="tasks")
