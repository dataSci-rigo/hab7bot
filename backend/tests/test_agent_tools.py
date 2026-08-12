import pytest
from sqlalchemy.orm import Session

from app.ai.agent_tools import ToolError, dispatch_tool
from app.schemas.role import RoleCreate
from app.services import roles as roles_service


@pytest.fixture()
def role(db_session: Session):
    return roles_service.create_role(db_session, RoleCreate(name="Engineer"))


def test_create_task_resolves_role_by_name(db_session: Session, role) -> None:
    result = dispatch_tool(
        db_session, "create_task", {"title": "Write tests", "role_name": "Engineer"}
    )
    assert result["title"] == "Write tests"
    assert result["role"] == "Engineer"
    assert result["quadrant"] == "Q2"


def test_create_task_unknown_role_raises(db_session: Session, role) -> None:
    with pytest.raises(ToolError):
        dispatch_tool(db_session, "create_task", {"title": "x", "role_name": "Nope"})


def test_list_tasks_filters_by_status(db_session: Session, role) -> None:
    dispatch_tool(db_session, "create_task", {"title": "A", "role_name": "Engineer"})
    result = dispatch_tool(db_session, "list_tasks", {"status": "planned"})
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["title"] == "A"


def test_search_tasks_matches_substring(db_session: Session, role) -> None:
    dispatch_tool(db_session, "create_task", {"title": "Call the dentist", "role_name": "Engineer"})
    dispatch_tool(db_session, "create_task", {"title": "Buy milk", "role_name": "Engineer"})
    result = dispatch_tool(db_session, "search_tasks", {"query": "dentist"})
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["title"] == "Call the dentist"


def test_update_task_by_id(db_session: Session, role) -> None:
    created = dispatch_tool(db_session, "create_task", {"title": "A", "role_name": "Engineer"})
    result = dispatch_tool(
        db_session, "update_task", {"task_id": created["id"], "quadrant": "Q1", "is_big_rock": True}
    )
    assert result["quadrant"] == "Q1"
    assert result["is_big_rock"] is True


def test_complete_task(db_session: Session, role) -> None:
    created = dispatch_tool(db_session, "create_task", {"title": "A", "role_name": "Engineer"})
    result = dispatch_tool(db_session, "complete_task", {"task_id": created["id"]})
    assert result["status"] == "done"


def test_drop_task(db_session: Session, role) -> None:
    created = dispatch_tool(db_session, "create_task", {"title": "A", "role_name": "Engineer"})
    result = dispatch_tool(db_session, "drop_task", {"task_id": created["id"]})
    assert result["status"] == "dropped"


def test_get_week_plan_splits_big_rocks(db_session: Session, role) -> None:
    dispatch_tool(
        db_session,
        "create_task",
        {
            "title": "Big",
            "role_name": "Engineer",
            "is_big_rock": True,
            "scheduled_week": "2026-W32",
        },
    )
    dispatch_tool(
        db_session,
        "create_task",
        {"title": "Small", "role_name": "Engineer", "scheduled_week": "2026-W32"},
    )
    result = dispatch_tool(db_session, "get_week_plan", {"iso_week": "2026-W32"})
    assert [t["title"] for t in result["big_rocks"]] == ["Big"]
    assert [t["title"] for t in result["scheduled_tasks"]] == ["Small"]


def test_set_big_rocks_pins_tasks(db_session: Session, role) -> None:
    a = dispatch_tool(db_session, "create_task", {"title": "A", "role_name": "Engineer"})
    result = dispatch_tool(db_session, "set_big_rocks", {"task_ids": [a["id"]]})
    assert result["updated"][0]["is_big_rock"] is True


def test_list_projects_filters_by_role_and_status(db_session: Session, role) -> None:
    dispatch_tool(
        db_session, "create_project", {"title": "Migrate to Postgres", "role_name": "Engineer"}
    )
    result = dispatch_tool(db_session, "list_projects", {"role_name": "Engineer"})
    assert [p["title"] for p in result["projects"]] == ["Migrate to Postgres"]

    result = dispatch_tool(db_session, "list_projects", {"status": "active"})
    assert result["projects"] == []


def test_create_and_update_project(db_session: Session, role) -> None:
    project = dispatch_tool(
        db_session, "create_project", {"title": "Migrate to Postgres", "role_name": "Engineer"}
    )
    assert project["status"] == "idea"
    updated = dispatch_tool(
        db_session, "update_project", {"project_id": project["id"], "status": "active"}
    )
    assert updated["status"] == "active"


def test_update_project_rejects_abandoned_status(db_session: Session, role) -> None:
    project = dispatch_tool(db_session, "create_project", {"title": "P", "role_name": "Engineer"})
    with pytest.raises(ToolError):
        dispatch_tool(
            db_session, "update_project", {"project_id": project["id"], "status": "abandoned"}
        )


def test_abandon_project(db_session: Session, role) -> None:
    project = dispatch_tool(db_session, "create_project", {"title": "P", "role_name": "Engineer"})
    result = dispatch_tool(db_session, "abandon_project", {"project_id": project["id"]})
    assert result["status"] == "abandoned"


def test_unknown_tool_raises(db_session: Session) -> None:
    with pytest.raises(ToolError):
        dispatch_tool(db_session, "not_a_real_tool", {})
