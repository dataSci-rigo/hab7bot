from datetime import UTC, datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import UUIDPKMixin


class ConversationMessage(UUIDPKMixin, Base):
    __tablename__ = "conversation_messages"

    role: Mapped[str] = mapped_column(String(20))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(String)
    # Python-side default (not server_default): a user/assistant pair is often
    # appended within the same second, and SQLite's CURRENT_TIMESTAMP only has
    # second resolution — that made history ordering nondeterministic on ties.
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


class ConversationSummary(UUIDPKMixin, Base):
    """Singleton — rolling summary of conversation history older than the
    window kept in ConversationMessage. See services/conversation.py."""

    __tablename__ = "conversation_summary"

    summary: Mapped[str] = mapped_column(String, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
