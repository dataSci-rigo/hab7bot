import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.client import call_tool
from app.ai.prompts import capture as capture_prompt
from app.ai.schemas import CaptureInference
from app.ai.tools.definitions import CAPTURE_TOOL
from app.config import settings
from app.services import projects as projects_service
from app.services import roles as roles_service

logger = logging.getLogger(__name__)


def infer_task_metadata(db: Session, text: str) -> CaptureInference | None:
    """§3.4 — cheap/fast-model call. Returns None on any failure; the caller
    (services/capture.py) must still create the task with defaults."""
    roles = roles_service.list_roles(db, active_only=True)
    projects = projects_service.list_projects(db)

    raw = call_tool(
        system=capture_prompt.SYSTEM,
        user_message=capture_prompt.build_user_message(text, roles, projects),
        tool_name=CAPTURE_TOOL["name"],
        tool_description=CAPTURE_TOOL["description"],
        input_schema=CAPTURE_TOOL["input_schema"],
        model=settings.anthropic_model_fast,
        timeout=10.0,
    )
    if raw is None:
        return None
    try:
        return CaptureInference.model_validate(raw)
    except ValidationError:
        logger.warning("Capture inference response failed schema validation", exc_info=True)
        return None
