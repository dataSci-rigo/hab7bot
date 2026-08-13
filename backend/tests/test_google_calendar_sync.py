from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.integrations.google import sync as google_sync
from app.models.enums import TaskOrigin
from app.schemas.role import RoleCreate
from app.schemas.task import TaskCreate
from app.services import google_links
from app.services import roles as roles_service
from app.services import tasks as tasks_service


@pytest.fixture()
def role(db_session: Session):
    return roles_service.create_role(db_session, RoleCreate(name="Engineer"))


def test_push_new_scheduled_task_creates_event_link(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = tasks_service.create_task(
        db_session,
        TaskCreate(title="Doctor appointment", role_id=role.id, scheduled_day=date(2026, 9, 1)),
    )

    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.ensure_calendar", lambda: "cal1"
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.insert_event",
        lambda *a, **k: {"id": "gevent1", "updated": "ts1"},
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.list_events", lambda cal_id: []
    )

    result = google_sync.sync_calendar(db_session)

    assert result["pushed_created"] == 1
    link = google_links.get_event_link(db_session, task.id)
    assert link.google_event_id == "gevent1"


def test_unscheduled_tasks_are_not_pushed_to_calendar(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    tasks_service.create_task(db_session, TaskCreate(title="No day set", role_id=role.id))

    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.ensure_calendar", lambda: "cal1"
    )
    insert_calls = []
    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.insert_event",
        lambda *a, **k: insert_calls.append(a) or {"id": "x", "updated": None},
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.list_events", lambda cal_id: []
    )

    google_sync.sync_calendar(db_session)

    assert insert_calls == []


def test_pull_new_calendar_event_creates_task_via_capture(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.ensure_calendar", lambda: "cal1"
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.insert_event",
        lambda *a, **k: {"id": "x", "updated": None},
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.list_events",
        lambda cal_id: [
            {
                "id": "gevent1",
                "summary": "Team offsite",
                "description": "Quarterly planning",
                "start": {"date": "2026-09-05"},
                "end": {"date": "2026-09-06"},
                "updated": "ts1",
            }
        ],
    )
    # Capture inference isn't under test here — force the degrade-to-defaults
    # path so this test doesn't depend on the AI call.
    monkeypatch.setattr("app.services.capture.infer_task_metadata", lambda db, text: None)

    result = google_sync.sync_calendar(db_session)

    assert result["pulled"] == 1
    tasks = tasks_service.list_tasks(db_session)
    pulled = next(t for t in tasks if "Team offsite" in t.title)
    assert pulled.scheduled_day == date(2026, 9, 5)
    assert pulled.origin == TaskOrigin.google


def test_pull_unchanged_event_is_skipped(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = tasks_service.create_task(
        db_session,
        TaskCreate(title="A", role_id=role.id, scheduled_day=date(2026, 9, 1)),
    )
    google_links.create_event_link(db_session, task.id, "gevent1", "cal1", "ts1")

    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.ensure_calendar", lambda: "cal1"
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.insert_event",
        lambda *a, **k: {"id": "x", "updated": None},
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_calendar.list_events",
        lambda cal_id: [
            {
                "id": "gevent1",
                "summary": "A",
                "start": {"date": "2026-09-01"},
                "end": {"date": "2026-09-02"},
                "updated": "ts1",
            }
        ],
    )

    result = google_sync.sync_calendar(db_session)

    assert result["pulled"] == 0
