from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin


class WeeklyReview(UUIDPKMixin, CreatedAtMixin, Base):
    """Populated by the Phase 5 analyze_week job — model defined now per SPEC §1."""

    __tablename__ = "weekly_reviews"

    iso_week: Mapped[str] = mapped_column(String(8), unique=True)
    # computed plan-vs-outcome stats
    stats: Mapped[dict | None] = mapped_column(JSON, default=None)
    # §3.3 WeekAnalysis output
    ai_analysis: Mapped[dict | None] = mapped_column(JSON, default=None)
    # user's own written reflection
    reflection: Mapped[str | None] = mapped_column(String, default=None)
