import pytest
from sqlalchemy.orm import Session

from app.integrations.google import sync as google_sync
from app.integrations.google.auth import GoogleAuthError
from app.models.enums import TaskOrigin, TaskStatus
from app.schemas.role import RoleCreate
from app.schemas.task import TaskCreate
from app.services import roles as roles_service
from app.services import tasks as tasks_service


@pytest.fixture()
def role(db_session: Session):
    return roles_service.create_role(db_session, RoleCreate(name="Engineer"))


# ── tasks: push ──────────────────────────────────────────────────────────────


def test_push_new_task_creates_link(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = tasks_service.create_task(
        db_session, TaskCreate(title="Write tests", role_id=role.id)
    )

    monkeypatch.setattr("app.integrations.google.sync.google_tasks.ensure_list", lambda: "list1")
    inserted = {"id": "gtask1", "updated": "2026-01-01T00:00:00Z"}
    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.insert_task",
        lambda *a, **k: inserted,
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.list_tasks", lambda list_id: []
    )

    result = google_sync.sync_tasks(db_session)

    assert result["pushed_created"] == 1
    from app.services import google_links

    link = google_links.get_task_link(db_session, task.id)
    assert link.google_task_id == "gtask1"


def test_dropped_tasks_are_not_pushed(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = tasks_service.create_task(db_session, TaskCreate(title="Old", role_id=role.id))
    from app.schemas.task import TaskUpdate

    tasks_service.update_task(db_session, task.id, TaskUpdate(status=TaskStatus.dropped))

    monkeypatch.setattr("app.integrations.google.sync.google_tasks.ensure_list", lambda: "list1")
    insert_calls = []
    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.insert_task",
        lambda *a, **k: insert_calls.append(a) or {"id": "x", "updated": None},
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.list_tasks", lambda list_id: []
    )

    google_sync.sync_tasks(db_session)

    assert insert_calls == []


def test_push_update_only_for_changed_tasks(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = tasks_service.create_task(db_session, TaskCreate(title="A", role_id=role.id))
    from app.services import google_links

    link = google_links.create_task_link(db_session, task.id, "gtask1", "list1", "old-ts")
    # simulate the link already being fully synced (last_synced_at now, task untouched since)
    google_links.touch_task_link(db_session, link, "old-ts")

    monkeypatch.setattr("app.integrations.google.sync.google_tasks.ensure_list", lambda: "list1")
    update_calls = []
    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.insert_task",
        lambda *a, **k: {"id": "unused", "updated": None},
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.update_task",
        lambda *a, **k: update_calls.append(a) or {"updated": "new-ts"},
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.list_tasks", lambda list_id: []
    )

    result = google_sync.sync_tasks(db_session)

    assert result["pushed_updated"] == 0
    assert update_calls == []

    # now actually change the task — should be pushed this time
    from app.schemas.task import TaskUpdate

    tasks_service.update_task(db_session, task.id, TaskUpdate(title="A (edited)"))
    result = google_sync.sync_tasks(db_session)
    assert result["pushed_updated"] == 1


# ── tasks: pull ──────────────────────────────────────────────────────────────


def test_pull_new_google_task_resolves_role_from_notes(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.integrations.google.sync.google_tasks.ensure_list", lambda: "list1")
    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.insert_task",
        lambda *a, **k: {"id": "x", "updated": None},
    )
    from app.integrations.google.notes_codec import TaskMetadata, encode

    notes = encode(TaskMetadata(role_name="Engineer", quadrant="Q1"), "extra notes")
    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.list_tasks",
        lambda list_id: [
            {"id": "gtask1", "title": "From Google", "notes": notes, "updated": "ts1"}
        ],
    )

    result = google_sync.sync_tasks(db_session)

    assert result["pulled"] == 1
    tasks = tasks_service.list_tasks(db_session)
    pulled = next(t for t in tasks if t.title == "From Google")
    assert pulled.role_id == role.id
    assert pulled.quadrant.value == "Q1"
    assert pulled.origin == TaskOrigin.google


def test_pull_unchanged_google_task_is_skipped(
    db_session: Session, role, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = tasks_service.create_task(db_session, TaskCreate(title="A", role_id=role.id))
    from app.services import google_links

    google_links.create_task_link(db_session, task.id, "gtask1", "list1", "ts1")

    monkeypatch.setattr("app.integrations.google.sync.google_tasks.ensure_list", lambda: "list1")
    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.insert_task",
        lambda *a, **k: {"id": "x", "updated": None},
    )
    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.list_tasks",
        lambda list_id: [{"id": "gtask1", "title": "A", "notes": None, "updated": "ts1"}],
    )

    result = google_sync.sync_tasks(db_session)

    assert result["pulled"] == 0


# ── sync_all degradation ────────────────────────────────────────────────────


def test_sync_all_degrades_gracefully_when_not_authorized(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    def raise_auth_error():
        raise GoogleAuthError("no token")

    monkeypatch.setattr(
        "app.integrations.google.sync.google_tasks.ensure_list", raise_auth_error
    )

    result = google_sync.sync_all(db_session)

    assert result["ok"] is False
    assert "no token" in result["reason"]
