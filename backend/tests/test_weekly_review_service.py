import pytest
from sqlalchemy.orm import Session

from app.ai.schemas import WeekAnalysis
from app.models.enums import Quadrant, TaskStatus
from app.schemas.role import RoleCreate
from app.schemas.task import TaskCreate
from app.services import roles as roles_service
from app.services import tasks as tasks_service
from app.services import weekly_review as weekly_review_service


def _make_role(db_session: Session, name: str = "Engineer"):
    return roles_service.create_role(db_session, RoleCreate(name=name))


def _fake_analysis(**overrides) -> WeekAnalysis:
    defaults = {
        "summary": "A week happened.",
        "q2_percent_trend": "flat",
    }
    return WeekAnalysis(**{**defaults, **overrides})


def test_compute_week_stats_counts_big_rocks_and_carry_over(db_session: Session) -> None:
    role = _make_role(db_session)
    rock = tasks_service.create_task(
        db_session,
        TaskCreate(title="Rock", role_id=role.id, is_big_rock=True, scheduled_week="2026-W33"),
    )
    tasks_service.complete_task(db_session, rock.id)
    tasks_service.create_task(
        db_session,
        TaskCreate(
            title="Still pending", role_id=role.id, status=TaskStatus.planned,
            scheduled_week="2026-W33",
        ),
    )

    stats = weekly_review_service.compute_week_stats(db_session, "2026-W33")

    assert stats["big_rock_total"] == 1
    assert stats["big_rock_completed"] == 1
    assert stats["big_rock_completion_rate"] == 1.0
    assert stats["carry_over_count"] == 1
    assert stats["avg_capture_to_completion_hours"] is not None


def test_compute_week_stats_effort_split_by_quadrant_and_role(db_session: Session) -> None:
    engineer = _make_role(db_session, "Engineer")
    parent = _make_role(db_session, "Parent")
    t1 = tasks_service.create_task(
        db_session,
        TaskCreate(
            title="A", role_id=engineer.id, quadrant=Quadrant.Q2,
            estimate_minutes=60, scheduled_week="2026-W33",
        ),
    )
    t2 = tasks_service.create_task(
        db_session,
        TaskCreate(
            title="B", role_id=parent.id, quadrant=Quadrant.Q1,
            estimate_minutes=30, scheduled_week="2026-W33",
        ),
    )
    tasks_service.complete_task(db_session, t1.id)
    tasks_service.complete_task(db_session, t2.id)

    stats = weekly_review_service.compute_week_stats(db_session, "2026-W33")

    assert stats["quadrant_effort_minutes"]["Q2"] == 60
    assert stats["quadrant_effort_minutes"]["Q1"] == 30
    assert stats["role_effort_minutes"] == {"Engineer": 60, "Parent": 30}


def test_generate_review_is_idempotent_unless_forced(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []
    monkeypatch.setattr(
        "app.services.weekly_review.analyze_week",
        lambda stats, previous, reflection: calls.append(1) or _fake_analysis(),
    )

    first = weekly_review_service.generate_review(db_session, "2026-W33")
    second = weekly_review_service.generate_review(db_session, "2026-W33")

    assert first.id == second.id
    assert len(calls) == 1

    third = weekly_review_service.generate_review(db_session, "2026-W33", force=True)
    assert third.id == first.id
    assert len(calls) == 2


def test_generate_review_stores_stats_even_when_ai_unavailable(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.services.weekly_review.analyze_week", lambda stats, previous, reflection: None
    )

    review = weekly_review_service.generate_review(db_session, "2026-W33")

    assert review.stats is not None
    assert review.ai_analysis is None


def test_generate_review_passes_previous_analyses_with_iso_week(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.services.weekly_review.analyze_week",
        lambda stats, previous, reflection: _fake_analysis(),
    )
    weekly_review_service.generate_review(db_session, "2026-W32")

    seen_previous = []
    monkeypatch.setattr(
        "app.services.weekly_review.analyze_week",
        lambda stats, previous, reflection: seen_previous.append(previous) or _fake_analysis(),
    )
    weekly_review_service.generate_review(db_session, "2026-W33")

    assert seen_previous[0][0]["iso_week"] == "2026-W32"


def test_set_reflection_creates_review_row_if_missing(db_session: Session) -> None:
    review = weekly_review_service.set_reflection(db_session, "2026-W33", "Good week overall.")

    assert review.reflection == "Good week overall."
    assert weekly_review_service.get_review(db_session, "2026-W33").id == review.id
