import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalUpdate


def create_goal(db: Session, data: GoalCreate) -> Goal:
    goal = Goal(**data.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_goal(db: Session, goal_id: uuid.UUID) -> Goal | None:
    return db.get(Goal, goal_id)


def list_goals(db: Session, role_id: uuid.UUID | None = None) -> list[Goal]:
    stmt = select(Goal)
    if role_id is not None:
        stmt = stmt.where(Goal.role_id == role_id)
    return list(db.scalars(stmt.order_by(Goal.created_at)))


def update_goal(db: Session, goal_id: uuid.UUID, data: GoalUpdate) -> Goal | None:
    goal = get_goal(db, goal_id)
    if goal is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, goal_id: uuid.UUID) -> bool:
    goal = get_goal(db, goal_id)
    if goal is None:
        return False
    db.delete(goal)
    db.commit()
    return True
