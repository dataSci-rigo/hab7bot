from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import ConversationMessage, ConversationSummary

WINDOW_SIZE = 20  # raw messages kept verbatim before older ones get summarized
SUMMARIZE_KEEP = 10  # how many of the most-recent messages survive a summarization pass


def append_message(db: Session, role: str, content: str) -> ConversationMessage:
    message = ConversationMessage(role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_recent_messages(db: Session, limit: int = WINDOW_SIZE) -> list[ConversationMessage]:
    stmt = select(ConversationMessage).order_by(ConversationMessage.created_at.desc()).limit(limit)
    return list(reversed(list(db.scalars(stmt))))


def get_summary(db: Session) -> ConversationSummary:
    summary = db.scalar(select(ConversationSummary).limit(1))
    if summary is None:
        summary = ConversationSummary(summary="")
        db.add(summary)
        db.commit()
        db.refresh(summary)
    return summary


def messages_needing_summarization(db: Session) -> list[ConversationMessage] | None:
    """Returns the oldest messages to fold into the summary, or None if the
    window isn't over threshold yet."""
    all_messages = list(
        db.scalars(select(ConversationMessage).order_by(ConversationMessage.created_at))
    )
    if len(all_messages) <= WINDOW_SIZE:
        return None
    return all_messages[: len(all_messages) - SUMMARIZE_KEEP]


def apply_summarization(
    db: Session, new_summary_text: str, folded: list[ConversationMessage]
) -> None:
    summary = get_summary(db)
    summary.summary = new_summary_text
    for message in folded:
        db.delete(message)
    db.commit()
