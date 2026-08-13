from sqlalchemy.orm import Session

from app.ai.agent_tools import dispatch_tool
from app.services import weekly_review as weekly_review_service
from app.services.clock import today
from app.services.iso_week import iso_week_string


def test_get_progress_analysis_reports_not_found_when_no_review_exists(
    db_session: Session,
) -> None:
    result = dispatch_tool(db_session, "get_progress_analysis", {"iso_week": "2026-W20"})

    assert result == {"iso_week": "2026-W20", "found": False}


def test_get_progress_analysis_returns_existing_review(db_session: Session) -> None:
    weekly_review_service.set_reflection(db_session, "2026-W20", "Went well.")

    result = dispatch_tool(db_session, "get_progress_analysis", {"iso_week": "2026-W20"})

    assert result["found"] is True
    assert result["reflection"] == "Went well."


def test_get_progress_analysis_defaults_to_current_week(db_session: Session) -> None:
    result = dispatch_tool(db_session, "get_progress_analysis", {})

    assert result["iso_week"] == iso_week_string(today())


def test_add_reflection_saves_to_weekly_review(db_session: Session) -> None:
    result = dispatch_tool(
        db_session, "add_reflection", {"iso_week": "2026-W21", "reflection": "Tough week."}
    )

    assert result == {"iso_week": "2026-W21", "reflection": "Tough week."}
    review = weekly_review_service.get_review(db_session, "2026-W21")
    assert review.reflection == "Tough week."


def test_log_daily_note_saves_to_daily_log(db_session: Session) -> None:
    result = dispatch_tool(db_session, "log_daily_note", {"note": "Shipped the report."})

    assert result["note"] == "Shipped the report."
    assert result["log_date"] == today().isoformat()
