import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.week_plan import RoleWeekIntention, WeekPlan


def get_or_create_week_plan(db: Session, iso_week: str) -> WeekPlan:
    week_plan = db.scalar(select(WeekPlan).where(WeekPlan.iso_week == iso_week))
    if week_plan is None:
        week_plan = WeekPlan(iso_week=iso_week)
        db.add(week_plan)
        db.commit()
        db.refresh(week_plan)
    return week_plan


def get_week_plan_view(db: Session, iso_week: str) -> dict:
    tasks = list(db.scalars(select(Task).where(Task.scheduled_week == iso_week)))
    big_rocks = [t for t in tasks if t.is_big_rock]
    scheduled_tasks = [t for t in tasks if not t.is_big_rock]

    week_plan = db.scalar(select(WeekPlan).where(WeekPlan.iso_week == iso_week))
    intentions = week_plan.role_intentions if week_plan else []

    return {
        "iso_week": iso_week,
        "big_rocks": big_rocks,
        "scheduled_tasks": scheduled_tasks,
        "role_intentions": intentions,
    }


def set_role_intention(
    db: Session, iso_week: str, role_id: uuid.UUID, note: str
) -> RoleWeekIntention:
    week_plan = get_or_create_week_plan(db, iso_week)
    intention = db.scalar(
        select(RoleWeekIntention).where(
            RoleWeekIntention.week_plan_id == week_plan.id,
            RoleWeekIntention.role_id == role_id,
        )
    )
    if intention is None:
        intention = RoleWeekIntention(week_plan_id=week_plan.id, role_id=role_id, note=note)
        db.add(intention)
    else:
        intention.note = note
    db.commit()
    db.refresh(intention)
    return intention
