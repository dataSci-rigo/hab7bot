import logging
import uuid

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.client import call_tool
from app.ai.prompts import breakdown as breakdown_prompt
from app.ai.schemas import BreakdownProposal
from app.ai.tools.definitions import BREAKDOWN_TOOL
from app.config import settings
from app.services import goals as goals_service
from app.services import mission as mission_service
from app.services import projects as projects_service
from app.services import roles as roles_service
from app.services import tasks as tasks_service

logger = logging.getLogger(__name__)


def breakdown_project(db: Session, project_id: uuid.UUID) -> BreakdownProposal | None:
    """§3.1 — nothing is written to the DB here; the caller decides what to accept."""
    project = projects_service.get_project(db, project_id)
    if project is None:
        return None
    role = roles_service.get_role(db, project.role_id)
    goal = goals_service.get_goal(db, project.goal_id) if project.goal_id else None
    mission = mission_service.get_mission(db)
    existing_tasks = tasks_service.list_tasks(db, project_id=project_id)

    raw = call_tool(
        system=breakdown_prompt.SYSTEM,
        user_message=breakdown_prompt.build_user_message(
            project, role, goal, mission, existing_tasks
        ),
        tool_name=BREAKDOWN_TOOL["name"],
        tool_description=BREAKDOWN_TOOL["description"],
        input_schema=BREAKDOWN_TOOL["input_schema"],
        model=settings.anthropic_model,
        timeout=90.0,
    )
    if raw is None:
        return None
    try:
        return BreakdownProposal.model_validate(raw)
    except ValidationError:
        logger.warning("Breakdown response failed schema validation", exc_info=True)
        return None
