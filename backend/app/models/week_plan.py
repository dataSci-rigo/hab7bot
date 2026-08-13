import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.role import Role


class WeekPlan(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "week_plans"

    iso_week: Mapped[str] = mapped_column(String(8), unique=True)  # "YYYY-Www"
    planning_prompt_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None
    )

    role_intentions: Mapped[list["RoleWeekIntention"]] = relationship(
        back_populates="week_plan", cascade="all, delete-orphan"
    )


class RoleWeekIntention(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "role_week_intentions"
    __table_args__ = (UniqueConstraint("week_plan_id", "role_id"),)

    week_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("week_plans.id"))
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"))
    note: Mapped[str] = mapped_column(String, default="")

    week_plan: Mapped["WeekPlan"] = relationship(back_populates="role_intentions")
    role: Mapped["Role"] = relationship()
