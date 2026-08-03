from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_session
from app.db import get_db
from app.schemas.settings import AppSettingsRead, AppSettingsUpdate
from app.services import settings as settings_service

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(require_session)])


@router.get("", response_model=AppSettingsRead)
def get_settings(db: Session = Depends(get_db)) -> AppSettingsRead:
    return settings_service.get_settings(db)


@router.put("", response_model=AppSettingsRead)
def update_settings(data: AppSettingsUpdate, db: Session = Depends(get_db)) -> AppSettingsRead:
    return settings_service.update_settings(db, data.week_start_day)
