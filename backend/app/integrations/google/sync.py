"""Push-then-pull two-way sync orchestration for Google Tasks + Calendar —
see SPEC §5. Pushing before pulling means a just-pushed local change is
never immediately overwritten by the pull that follows it in the same run.

Degrades gracefully like AI calls do: any Google API failure (including "not
authorized yet") is caught and reported in the returned dict rather than
raised, so a scheduled sync run never crashes the bot worker.
"""
import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.ai.resolve import resolve_project, resolve_role
from app.integrations.google import calendar as google_calendar
from app.integrations.google import tasks as google_tasks
from app.integrations.google.auth import GoogleAuthError
from app.integrations.google.notes_codec import TaskMetadata, decode, encode
from app.models.enums import Quadrant, TaskOrigin, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import capture as capture_service
from app.services import google_links
from app.services import projects as projects_service
from app.services import roles as roles_service
from app.services import tasks as tasks_service

logger = logging.getLogger(__name__)


def sync_all(db: Session) -> dict[str, Any]:
    try:
        tasks_result = sync_tasks(db)
        calendar_result = sync_calendar(db)
        return {"ok": True, "tasks": tasks_result, "calendar": calendar_result}
    except GoogleAuthError as e:
        logger.info("Skipping Google sync: %s", e)
        return {"ok": False, "reason": str(e)}
    except Exception:
        logger.warning("Google sync failed", exc_info=True)
        return {"ok": False, "reason": "Google sync failed — see logs."}


# ── tasks ────────────────────────────────────────────────────────────────────


def sync_tasks(db: Session) -> dict[str, int]:
    list_id = google_tasks.ensure_list()
    created = _push_new_tasks(db, list_id)
    updated = _push_task_updates(db, list_id)
    pulled = _pull_task_changes(db, list_id)
    return {"pushed_created": created, "pushed_updated": updated, "pulled": pulled}


def _task_metadata(db: Session, task) -> TaskMetadata:
    role = roles_service.get_role(db, task.role_id)
    project = projects_service.get_project(db, task.project_id) if task.project_id else None
    return TaskMetadata(
        role_name=role.name if role else None,
        quadrant=task.quadrant.value,
        is_big_rock=task.is_big_rock,
        project_title=project.title if project else None,
    )


def _push_new_tasks(db: Session, list_id: str) -> int:
    linked_ids = {link.task_id for link in google_links.list_task_links(db)}
    count = 0
    for task in tasks_service.list_tasks(db):
        if task.id in linked_ids or task.status == TaskStatus.dropped:
            continue
        notes = encode(_task_metadata(db, task), task.notes)
        result = google_tasks.insert_task(
            list_id, task.title, notes, completed=task.status == TaskStatus.done
        )
        google_links.create_task_link(db, task.id, result["id"], list_id, result.get("updated"))
        count += 1
    return count


def _push_task_updates(db: Session, list_id: str) -> int:
    count = 0
    for link in google_links.list_task_links(db):
        task = tasks_service.get_task(db, link.task_id)
        if task is None or task.updated_at <= link.last_synced_at:
            continue
        notes = encode(_task_metadata(db, task), task.notes)
        result = google_tasks.update_task(
            list_id,
            link.google_task_id,
            title=task.title,
            notes=notes,
            completed=task.status == TaskStatus.done,
        )
        google_links.touch_task_link(db, link, result.get("updated"))
        count += 1
    return count


def _apply_pulled_task_fields(
    db: Session, task, title: str, metadata: TaskMetadata, completed: bool
) -> None:
    role_id = task.role_id
    if metadata.role_name:
        role = resolve_role(metadata.role_name, roles_service.list_roles(db, active_only=True))
        if role:
            role_id = role.id
    project_id = task.project_id
    if metadata.project_title:
        project = resolve_project(metadata.project_title, projects_service.list_projects(db))
        if project:
            project_id = project.id
    quadrant = Quadrant(metadata.quadrant) if metadata.quadrant else task.quadrant

    tasks_service.update_task(
        db,
        task.id,
        TaskUpdate(
            title=title,
            role_id=role_id,
            project_id=project_id,
            quadrant=quadrant,
            is_big_rock=metadata.is_big_rock,
        ),
    )
    was_done = task.status == TaskStatus.done
    if completed and not was_done:
        tasks_service.complete_task(db, task.id)
    elif not completed and was_done:
        tasks_service.uncomplete_task(db, task.id)


def _pull_task_changes(db: Session, list_id: str) -> int:
    count = 0
    for gtask in google_tasks.list_tasks(list_id):
        google_updated = gtask.get("updated")
        completed = gtask.get("status") == "completed"
        title = gtask.get("title") or "(untitled)"
        metadata, _free_notes = decode(gtask.get("notes"))

        link = google_links.get_task_link_by_google_id(db, gtask["id"])
        if link is None:
            roles = roles_service.list_roles(db, active_only=True)
            role = resolve_role(metadata.role_name, roles) if metadata.role_name else None
            role_id = role.id if role else (roles[0].id if roles else None)
            project = None
            if metadata.project_title:
                existing_projects = projects_service.list_projects(db)
                project = resolve_project(metadata.project_title, existing_projects)
            task = tasks_service.create_task(
                db,
                TaskCreate(
                    title=title,
                    role_id=role_id,
                    project_id=project.id if project else None,
                    quadrant=Quadrant(metadata.quadrant) if metadata.quadrant else Quadrant.Q2,
                    is_big_rock=metadata.is_big_rock,
                    status=TaskStatus.done if completed else TaskStatus.inbox,
                    origin=TaskOrigin.google,
                ),
            )
            google_links.create_task_link(db, task.id, gtask["id"], list_id, google_updated)
            count += 1
            continue

        if google_updated and link.google_updated_at and google_updated <= link.google_updated_at:
            continue  # unchanged on Google's side since last sync

        task = tasks_service.get_task(db, link.task_id)
        if task is None:
            continue
        _apply_pulled_task_fields(db, task, title, metadata, completed)
        google_links.touch_task_link(db, link, google_updated)
        count += 1
    return count


# ── calendar ─────────────────────────────────────────────────────────────────


def sync_calendar(db: Session) -> dict[str, int]:
    calendar_id = google_calendar.ensure_calendar()
    created = _push_new_events(db, calendar_id)
    updated = _push_event_updates(db, calendar_id)
    pulled = _pull_event_changes(db, calendar_id)
    return {"pushed_created": created, "pushed_updated": updated, "pulled": pulled}


def _push_new_events(db: Session, calendar_id: str) -> int:
    linked_ids = {link.task_id for link in google_links.list_event_links(db)}
    count = 0
    for task in tasks_service.list_tasks(db):
        if task.id in linked_ids or task.status == TaskStatus.dropped or not task.scheduled_day:
            continue
        result = google_calendar.insert_event(
            calendar_id, task.title, task.notes, task.scheduled_day, task.estimate_minutes
        )
        google_links.create_event_link(
            db, task.id, result["id"], calendar_id, result.get("updated")
        )
        count += 1
    return count


def _push_event_updates(db: Session, calendar_id: str) -> int:
    count = 0
    for link in google_links.list_event_links(db):
        task = tasks_service.get_task(db, link.task_id)
        if task is None or not task.scheduled_day or task.updated_at <= link.last_synced_at:
            continue
        result = google_calendar.update_event(
            calendar_id,
            link.google_event_id,
            task.title,
            task.notes,
            task.scheduled_day,
            task.estimate_minutes,
        )
        google_links.touch_event_link(db, link, result.get("updated"))
        count += 1
    return count


def _event_date(event: dict) -> date | None:
    start = event.get("start", {})
    if "date" in start:
        return date.fromisoformat(start["date"])
    if "dateTime" in start:
        return datetime.fromisoformat(start["dateTime"]).date()
    return None


def _event_duration_minutes(event: dict) -> int | None:
    start, end = event.get("start", {}), event.get("end", {})
    if "dateTime" not in start or "dateTime" not in end:
        return None
    delta: timedelta = datetime.fromisoformat(end["dateTime"]) - datetime.fromisoformat(
        start["dateTime"]
    )
    return int(delta.total_seconds() // 60)


def _pull_event_changes(db: Session, calendar_id: str) -> int:
    count = 0
    for event in google_calendar.list_events(calendar_id):
        google_updated = event.get("updated")
        scheduled_day = _event_date(event)
        if scheduled_day is None:
            continue

        link = google_links.get_event_link_by_google_id(db, event["id"])
        if link is None:
            title = event.get("summary", "(untitled event)")
            text = f"{title}: {event['description']}" if event.get("description") else title
            task = capture_service.capture_task(db, text, origin=TaskOrigin.google)
            tasks_service.update_task(
                db,
                task.id,
                TaskUpdate(
                    scheduled_day=scheduled_day,
                    estimate_minutes=_event_duration_minutes(event),
                ),
            )
            google_links.create_event_link(db, task.id, event["id"], calendar_id, google_updated)
            count += 1
            continue

        if google_updated and link.google_updated_at and google_updated <= link.google_updated_at:
            continue

        task = tasks_service.get_task(db, link.task_id)
        if task is None:
            continue
        tasks_service.update_task(
            db,
            task.id,
            TaskUpdate(
                title=event.get("summary", task.title),
                scheduled_day=scheduled_day,
                estimate_minutes=_event_duration_minutes(event) or task.estimate_minutes,
            ),
        )
        google_links.touch_event_link(db, link, google_updated)
        count += 1
    return count
