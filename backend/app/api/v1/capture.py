from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_session_or_api_key
from app.db import get_db
from app.models.enums import TaskOrigin
from app.schemas.capture import CaptureRequest
from app.schemas.task import TaskRead
from app.services import capture as capture_service

# Capture is the one route trusted local bots (brain-dump) may call with the
# internal X-Api-Key; every other v1 route stays session-cookie only.
router = APIRouter(tags=["capture"], dependencies=[Depends(require_session_or_api_key)])


@router.post("/capture", response_model=TaskRead, status_code=201)
def capture(data: CaptureRequest, db: Session = Depends(get_db)) -> TaskRead:
    return capture_service.capture_task(db, data.text, origin=TaskOrigin(data.origin))
