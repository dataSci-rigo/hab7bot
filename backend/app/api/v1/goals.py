import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_session
from app.db import get_db
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate
from app.services import goals as goals_service

router = APIRouter(prefix="/goals", tags=["goals"], dependencies=[Depends(require_session)])


@router.get("", response_model=list[GoalRead])
def list_goals(role_id: uuid.UUID | None = None, db: Session = Depends(get_db)) -> list[GoalRead]:
    return goals_service.list_goals(db, role_id=role_id)


@router.post("", response_model=GoalRead, status_code=201)
def create_goal(data: GoalCreate, db: Session = Depends(get_db)) -> GoalRead:
    return goals_service.create_goal(db, data)


@router.get("/{goal_id}", response_model=GoalRead)
def get_goal(goal_id: uuid.UUID, db: Session = Depends(get_db)) -> GoalRead:
    goal = goals_service.get_goal(db, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.put("/{goal_id}", response_model=GoalRead)
def update_goal(goal_id: uuid.UUID, data: GoalUpdate, db: Session = Depends(get_db)) -> GoalRead:
    goal = goals_service.update_goal(db, goal_id, data)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    if not goals_service.delete_goal(db, goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
