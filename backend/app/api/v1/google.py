from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_session
from app.db import get_db
from app.integrations.google.auth import is_authorized
from app.integrations.google.sync import sync_all
from app.schemas.google import GoogleStatus, GoogleSyncResult
from app.services import google_links

router = APIRouter(prefix="/google", tags=["google"], dependencies=[Depends(require_session)])


@router.get("/status", response_model=GoogleStatus)
def get_status(db: Session = Depends(get_db)) -> GoogleStatus:
    return GoogleStatus(
        connected=is_authorized(), last_synced_at=google_links.last_synced_at(db)
    )


@router.post("/sync", response_model=GoogleSyncResult)
def trigger_sync(db: Session = Depends(get_db)) -> GoogleSyncResult:
    return GoogleSyncResult.model_validate(sync_all(db))
