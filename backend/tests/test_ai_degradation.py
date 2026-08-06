import pytest
from sqlalchemy.orm import Session

from app.ai.client import call_tool
from app.config import settings
from app.models.enums import Quadrant, TaskStatus
from app.schemas.role import RoleCreate
from app.services import capture as capture_service
from app.services import roles as roles_service


@pytest.fixture()
def no_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "anthropic_api_key", "")


def test_call_tool_returns_none_without_api_key(no_api_key) -> None:
    result = call_tool(
        system="irrelevant",
        user_message="irrelevant",
        tool_name="whatever",
        tool_description="whatever",
        input_schema={"type": "object", "properties": {}},
        model="claude-sonnet-4-6",
    )
    assert result is None


def test_capture_still_creates_task_with_defaults_when_ai_unavailable(
    db_session: Session, no_api_key
) -> None:
    role = roles_service.create_role(db_session, RoleCreate(name="Engineer"))

    task = capture_service.capture_task(db_session, "call the accountant re: Q3 taxes")

    assert task.id is not None
    assert task.title == "call the accountant re: Q3 taxes"
    assert task.status == TaskStatus.inbox
    assert task.quadrant == Quadrant.Q2
    assert task.is_big_rock is False
    assert task.role_id == role.id  # falls back to the only (first active) role
