from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_session
from app.db import get_db
from app.schemas.inbox_triage import InboxTriageSuggestion
from app.services import inbox_triage as inbox_triage_service

router = APIRouter(prefix="/inbox", tags=["inbox"], dependencies=[Depends(require_session)])


@router.post("/ai-triage", response_model=list[InboxTriageSuggestion])
def ai_triage(db: Session = Depends(get_db)) -> list[InboxTriageSuggestion]:
    suggestions = inbox_triage_service.get_inbox_triage_suggestions(db)
    if suggestions is None:
        raise HTTPException(status_code=503, detail="AI is currently unavailable. Try again.")
    return suggestions
