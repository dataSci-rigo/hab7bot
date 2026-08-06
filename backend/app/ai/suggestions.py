import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.client import call_tool
from app.ai.prompts import suggestions as suggestions_prompt
from app.ai.schemas import ProjectSuggestionsOutput
from app.ai.tools.definitions import SUGGESTIONS_TOOL
from app.config import settings
from app.models.enums import ProjectStatus
from app.services import goals as goals_service
from app.services import mission as mission_service
from app.services import projects as projects_service
from app.services import roles as roles_service

logger = logging.getLogger(__name__)


def suggest_projects(db: Session) -> ProjectSuggestionsOutput | None:
    """§3.2 — read-only; nothing is written until a suggestion is accepted."""
    mission = mission_service.get_mission(db)
    roles = roles_service.list_roles(db, active_only=True)
    goals = goals_service.list_goals(db)
    active_projects = [
        p
        for p in projects_service.list_projects(db)
        if p.status in (ProjectStatus.idea, ProjectStatus.active)
    ]

    raw = call_tool(
        system=suggestions_prompt.SYSTEM,
        user_message=suggestions_prompt.build_user_message(mission, roles, goals, active_projects),
        tool_name=SUGGESTIONS_TOOL["name"],
        tool_description=SUGGESTIONS_TOOL["description"],
        input_schema=SUGGESTIONS_TOOL["input_schema"],
        model=settings.anthropic_model,
        timeout=60.0,
    )
    if raw is None:
        return None
    try:
        return ProjectSuggestionsOutput.model_validate(raw)
    except ValidationError:
        logger.warning("Project suggestions response failed schema validation", exc_info=True)
        return None
