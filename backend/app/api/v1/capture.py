from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_session
from app.db import get_db
from app.schemas.capture import CaptureRequest
from app.schemas.task import TaskRead
from app.services import capture as capture_service

router = APIRouter(tags=["capture"], dependencies=[Depends(require_session)])


@router.post("/capture", response_model=TaskRead, status_code=201)
def capture(data: CaptureRequest, db: Session = Depends(get_db)) -> TaskRead:
    return capture_service.capture_task(db, data.text)
