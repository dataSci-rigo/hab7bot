from sqlalchemy.orm import Session

from app.services import conversation as conversation_service


def test_window_not_over_threshold_returns_none(db_session: Session) -> None:
    for i in range(5):
        conversation_service.append_message(db_session, "user", f"msg {i}")
    assert conversation_service.messages_needing_summarization(db_session) is None


def test_window_over_threshold_returns_oldest_messages(db_session: Session) -> None:
    for i in range(25):
        conversation_service.append_message(db_session, "user", f"msg {i}")

    to_fold = conversation_service.messages_needing_summarization(db_session)
    assert to_fold is not None
    assert len(to_fold) == 15  # 25 - SUMMARIZE_KEEP(10)
    assert to_fold[0].content == "msg 0"
    assert to_fold[-1].content == "msg 14"


def test_apply_summarization_deletes_folded_and_updates_summary(db_session: Session) -> None:
    for i in range(25):
        conversation_service.append_message(db_session, "user", f"msg {i}")
    to_fold = conversation_service.messages_needing_summarization(db_session)

    conversation_service.apply_summarization(db_session, "summary of early messages", to_fold)

    remaining = conversation_service.get_recent_messages(db_session, limit=100)
    assert len(remaining) == 10
    assert remaining[0].content == "msg 15"
    assert conversation_service.get_summary(db_session).summary == "summary of early messages"
