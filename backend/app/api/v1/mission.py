from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_session
from app.db import get_db
from app.schemas.mission import MissionRead, MissionUpdate
from app.services import mission as mission_service

router = APIRouter(prefix="/mission", tags=["mission"], dependencies=[Depends(require_session)])


@router.get("", response_model=MissionRead)
def get_mission(db: Session = Depends(get_db)) -> MissionRead:
    return mission_service.get_mission(db)


@router.put("", response_model=MissionRead)
def update_mission(data: MissionUpdate, db: Session = Depends(get_db)) -> MissionRead:
    return mission_service.update_mission(db, data.content)
