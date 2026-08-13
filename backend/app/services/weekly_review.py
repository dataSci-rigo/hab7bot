from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.analysis import analyze_week
from app.models.enums import Quadrant, TaskStatus
from app.models.task import Task
from app.models.weekly_review import WeeklyReview


def _week_date_range(iso_week: str) -> tuple[date, date]:
    year_str, week_str = iso_week.split("-W")
    year, week = int(year_str), int(week_str)
    return date.fromisocalendar(year, week, 1), date.fromisocalendar(year, week, 7)


def compute_week_stats(db: Session, iso_week: str) -> dict:
    tasks = list(db.scalars(select(Task).where(Task.scheduled_week == iso_week)))
    big_rocks = [t for t in tasks if t.is_big_rock]
    big_rocks_completed = sum(1 for t in big_rocks if t.status == TaskStatus.done)
    completed = [t for t in tasks if t.status == TaskStatus.done]

    quadrant_effort_minutes = {q.value: 0 for q in Quadrant}
    role_effort_minutes: dict[str, int] = {}
    for t in completed:
        minutes = t.actual_minutes if t.actual_minutes is not None else (t.estimate_minutes or 0)
        quadrant_effort_minutes[t.quadrant.value] += minutes
        role_effort_minutes[t.role.name] = role_effort_minutes.get(t.role.name, 0) + minutes

    carry_over_count = sum(
        1
        for t in tasks
        if t.status in (TaskStatus.inbox, TaskStatus.planned, TaskStatus.in_progress)
    )

    _, sunday = _week_date_range(iso_week)
    week_end = datetime.combine(sunday, datetime.max.time())
    latencies_hours = [
        (t.completed_at - t.created_at).total_seconds() / 3600
        for t in completed
        if t.completed_at is not None and t.completed_at <= week_end
    ]

    return {
        "iso_week": iso_week,
        "big_rock_total": len(big_rocks),
        "big_rock_completed": big_rocks_completed,
        "big_rock_completion_rate": (
            big_rocks_completed / len(big_rocks) if big_rocks else None
        ),
        "quadrant_effort_minutes": quadrant_effort_minutes,
        "role_effort_minutes": role_effort_minutes,
        "carry_over_count": carry_over_count,
        "avg_capture_to_completion_hours": (
            sum(latencies_hours) / len(latencies_hours) if latencies_hours else None
        ),
    }


def get_review(db: Session, iso_week: str) -> WeeklyReview | None:
    return db.scalar(select(WeeklyReview).where(WeeklyReview.iso_week == iso_week))


def get_previous_reviews(db: Session, iso_week: str, limit: int = 3) -> list[WeeklyReview]:
    return list(
        db.scalars(
            select(WeeklyReview)
            .where(WeeklyReview.iso_week < iso_week)
            .order_by(WeeklyReview.iso_week.desc())
            .limit(limit)
        )
    )


def _get_or_create_review(db: Session, iso_week: str) -> WeeklyReview:
    review = get_review(db, iso_week)
    if review is None:
        review = WeeklyReview(iso_week=iso_week)
        db.add(review)
        db.commit()
        db.refresh(review)
    return review


def generate_review(db: Session, iso_week: str, force: bool = False) -> WeeklyReview:
    """Idempotent per SPEC §4: a WeeklyReview already existing for `iso_week`
    is returned as-is unless `force=True` (backs the web "Regenerate" button).
    """
    existing = get_review(db, iso_week)
    if existing is not None and not force:
        return existing

    stats = compute_week_stats(db, iso_week)
    previous = get_previous_reviews(db, iso_week, limit=3)
    previous_analyses = [
        {**r.ai_analysis, "iso_week": r.iso_week} for r in previous if r.ai_analysis is not None
    ]
    reflection = existing.reflection if existing else None

    analysis = analyze_week(stats, previous_analyses, reflection)

    review = existing or _get_or_create_review(db, iso_week)
    review.stats = stats
    if analysis is not None:
        review.ai_analysis = analysis.model_dump()
    db.commit()
    db.refresh(review)
    return review


def set_reflection(db: Session, iso_week: str, reflection: str) -> WeeklyReview:
    review = _get_or_create_review(db, iso_week)
    review.reflection = reflection
    db.commit()
    db.refresh(review)
    return review
