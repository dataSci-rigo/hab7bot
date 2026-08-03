import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_session
from app.db import get_db
from app.schemas.week_plan import RoleIntentionSet, WeekPlanRead
from app.services import week_plans as week_plans_service

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
