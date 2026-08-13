from sqlalchemy.orm import Session

from app.schemas.role import RoleCreate
from app.schemas.task import TaskCreate
from app.services import google_links
from app.services import roles as roles_service
from app.services import tasks as tasks_service


def _make_task(db_session: Session):
    role = roles_service.create_role(db_session, RoleCreate(name="Engineer"))
    return tasks_service.create_task(db_session, TaskCreate(title="A", role_id=role.id))


def test_create_and_get_task_link(db_session: Session) -> None:
    task = _make_task(db_session)
    link = google_links.create_task_link(db_session, task.id, "gtask1", "list1", "updated1")

    assert google_links.get_task_link(db_session, task.id).id == link.id
    assert google_links.get_task_link_by_google_id(db_session, "gtask1").id == link.id


def test_touch_task_link_updates_timestamps(db_session: Session) -> None:
    task = _make_task(db_session)
    link = google_links.create_task_link(db_session, task.id, "gtask1", "list1", "updated1")
    original_synced_at = link.last_synced_at

    touched = google_links.touch_task_link(db_session, link, "updated2")

    assert touched.google_updated_at == "updated2"
    assert touched.last_synced_at >= original_synced_at


def test_create_and_get_event_link(db_session: Session) -> None:
    task = _make_task(db_session)
    link = google_links.create_event_link(db_session, task.id, "gevent1", "cal1", "updated1")

    assert google_links.get_event_link(db_session, task.id).id == link.id
    assert google_links.get_event_link_by_google_id(db_session, "gevent1").id == link.id


def test_last_synced_at_none_when_no_links(db_session: Session) -> None:
    assert google_links.last_synced_at(db_session) is None


def test_last_synced_at_returns_most_recent_across_both_tables(db_session: Session) -> None:
    role = roles_service.create_role(db_session, RoleCreate(name="Engineer"))
    task1 = tasks_service.create_task(db_session, TaskCreate(title="A", role_id=role.id))
    task2 = tasks_service.create_task(db_session, TaskCreate(title="B", role_id=role.id))
    google_links.create_task_link(db_session, task1.id, "gtask1", "list1", None)
    event_link = google_links.create_event_link(db_session, task2.id, "gevent1", "cal1", None)

    assert google_links.last_synced_at(db_session) == event_link.last_synced_at
