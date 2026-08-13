import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_session
from app.db import get_db
from app.schemas.week_plan import RoleIntentionSet, WeekPlanRead
from app.schemas.weekly_review import ReflectionUpdate, WeeklyReviewRead
from app.services import week_plans as week_plans_service
from app.services import weekly_review as weekly_review_service

router = APIRouter(prefix="/weeks", tags=["weeks"], dependencies=[Depends(require_session)])


@router.get("/{iso_week}/plan", response_model=WeekPlanRead)
def get_week_plan(iso_week: str, db: Session = Depends(get_db)) -> WeekPlanRead:
    return week_plans_service.get_week_plan_view(db, iso_week)


@router.put("/{iso_week}/intentions/{role_id}")
def set_role_intention(
    iso_week: str, role_id: uuid.UUID, data: RoleIntentionSet, db: Session = Depends(get_db)
) -> dict[str, bool]:
    week_plans_service.set_role_intention(db, iso_week, role_id, data.note)
    return {"ok": True}


@router.get("/{iso_week}/review", response_model=WeeklyReviewRead)
def get_weekly_review(iso_week: str, db: Session = Depends(get_db)) -> WeeklyReviewRead:
    review = weekly_review_service.get_review(db, iso_week)
    if review is None:
        raise HTTPException(status_code=404, detail="No review generated for this week yet")
    return review


@router.post("/{iso_week}/review/generate", response_model=WeeklyReviewRead)
def generate_weekly_review(
    iso_week: str, force: bool = False, db: Session = Depends(get_db)
) -> WeeklyReviewRead:
    return weekly_review_service.generate_review(db, iso_week, force=force)


@router.put("/{iso_week}/review/reflection", response_model=WeeklyReviewRead)
def set_weekly_review_reflection(
    iso_week: str, data: ReflectionUpdate, db: Session = Depends(get_db)
) -> WeeklyReviewRead:
    return weekly_review_service.set_reflection(db, iso_week, data.reflection)
