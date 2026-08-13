from sqlalchemy.orm import Session

from app.models.enums import TaskStatus
from app.schemas.project import ProjectCreate
from app.schemas.role import RoleCreate
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import projects as projects_service
from app.services import roles as roles_service
from app.services import tasks as tasks_service


def _make_role(db_session: Session):
    return roles_service.create_role(db_session, RoleCreate(name="Engineer"))


def test_create_task_defaults(db_session: Session) -> None:
    role = _make_role(db_session)
    task = tasks_service.create_task(db_session, TaskCreate(title="Write tests", role_id=role.id))
    assert task.status == TaskStatus.inbox
    assert task.is_big_rock is False
    assert task.completed_at is None


def test_list_tasks_filters_by_scheduled_week(db_session: Session) -> None:
    role = _make_role(db_session)
    tasks_service.create_task(
        db_session, TaskCreate(title="A", role_id=role.id, scheduled_week="2026-W32")
    )
    tasks_service.create_task(
        db_session, TaskCreate(title="B", role_id=role.id, scheduled_week="2026-W33")
    )

    week32 = tasks_service.list_tasks(db_session, scheduled_week="2026-W32")
    assert len(week32) == 1
    assert week32[0].title == "A"


def test_complete_task_sets_status_and_timestamp(db_session: Session) -> None:
    role = _make_role(db_session)
    task = tasks_service.create_task(db_session, TaskCreate(title="Finish me", role_id=role.id))
    completed = tasks_service.complete_task(db_session, task.id)
    assert completed is not None
    assert completed.status == TaskStatus.done
    assert completed.completed_at is not None


def test_uncomplete_task_clears_status_and_timestamp(db_session: Session) -> None:
    role = _make_role(db_session)
    task = tasks_service.create_task(db_session, TaskCreate(title="Finish me", role_id=role.id))
    tasks_service.complete_task(db_session, task.id)
    reverted = tasks_service.uncomplete_task(db_session, task.id)
    assert reverted is not None
    assert reverted.status == TaskStatus.planned
    assert reverted.completed_at is None


def test_update_task_partial(db_session: Session) -> None:
    role = _make_role(db_session)
    task = tasks_service.create_task(db_session, TaskCreate(title="Original", role_id=role.id))
    updated = tasks_service.update_task(db_session, task.id, TaskUpdate(is_big_rock=True))
    assert updated is not None
    assert updated.is_big_rock is True
    assert updated.title == "Original"


def test_update_task_assigning_week_leaves_inbox(db_session: Session) -> None:
    role = _make_role(db_session)
    task = tasks_service.create_task(db_session, TaskCreate(title="A", role_id=role.id))
    assert task.status == TaskStatus.inbox

    updated = tasks_service.update_task(
        db_session, task.id, TaskUpdate(scheduled_week="2026-W34")
    )
    assert updated.status == TaskStatus.planned


def test_update_task_assigning_project_leaves_inbox(db_session: Session) -> None:
    role = _make_role(db_session)
    task = tasks_service.create_task(db_session, TaskCreate(title="A", role_id=role.id))

    project = projects_service.create_project(
        db_session, ProjectCreate(title="P", role_id=role.id)
    )
    updated = tasks_service.update_task(
        db_session, task.id, TaskUpdate(project_id=project.id)
    )
    assert updated.status == TaskStatus.planned


def test_update_task_explicit_status_not_overridden(db_session: Session) -> None:
    role = _make_role(db_session)
    task = tasks_service.create_task(db_session, TaskCreate(title="A", role_id=role.id))
    updated = tasks_service.update_task(
        db_session,
        task.id,
        TaskUpdate(scheduled_week="2026-W34", status=TaskStatus.dropped),
    )
    assert updated.status == TaskStatus.dropped


def test_update_task_does_not_reopen_non_inbox_tasks(db_session: Session) -> None:
    role = _make_role(db_session)
    task = tasks_service.create_task(db_session, TaskCreate(title="A", role_id=role.id))
    tasks_service.complete_task(db_session, task.id)

    updated = tasks_service.update_task(
        db_session, task.id, TaskUpdate(scheduled_week="2026-W34")
    )
    assert updated.status == TaskStatus.done
