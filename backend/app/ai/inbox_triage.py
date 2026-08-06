import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.client import call_tool
from app.ai.prompts import inbox_triage as inbox_triage_prompt
from app.ai.schemas import InboxTriageOutput
from app.ai.tools.definitions import INBOX_TRIAGE_TOOL
from app.config import settings
from app.models.enums import TaskStatus
from app.services import projects as projects_service
from app.services import roles as roles_service
from app.services import tasks as tasks_service

logger = logging.getLogger(__name__)


def triage_inbox(db: Session) -> InboxTriageOutput | None:
    """SPEC §2.2.2 'AI triage' — one call covering every inbox task.
    Read-only: nothing is written until the user accepts per-task."""
    inbox_tasks = tasks_service.list_tasks(db, status=TaskStatus.inbox)
    if not inbox_tasks:
        return InboxTriageOutput(items=[])

    roles = roles_service.list_roles(db, active_only=True)
    projects = projects_service.list_projects(db)

    raw = call_tool(
        system=inbox_triage_prompt.SYSTEM,
        user_message=inbox_triage_prompt.build_user_message(inbox_tasks, roles, projects),
        tool_name=INBOX_TRIAGE_TOOL["name"],
        tool_description=INBOX_TRIAGE_TOOL["description"],
        input_schema=INBOX_TRIAGE_TOOL["input_schema"],
        model=settings.anthropic_model,
        timeout=60.0,
    )
    if raw is None:
        return None
    try:
        return InboxTriageOutput.model_validate(raw)
    except ValidationError:
        logger.warning("Inbox triage response failed schema validation", exc_info=True)
        return None
