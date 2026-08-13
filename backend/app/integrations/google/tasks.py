"""Thin CRUD wrapper around the Google Tasks API v1 — mirrors
semantic_task_manager/google_tasks.py. Sync logic lives in sync.py."""
from app.integrations.google.auth import get_tasks_service

LIST_NAME = "Compass"


def ensure_list() -> str:
    service = get_tasks_service()
    result = service.tasklists().list(maxResults=100).execute()
    for tl in result.get("items", []):
        if tl["title"] == LIST_NAME:
            return tl["id"]
    created = service.tasklists().insert(body={"title": LIST_NAME}).execute()
    return created["id"]


def insert_task(list_id: str, title: str, notes: str | None, completed: bool) -> dict:
    service = get_tasks_service()
    body: dict = {"title": title}
    if notes:
        body["notes"] = notes
    if completed:
        body["status"] = "completed"
    return service.tasks().insert(tasklist=list_id, body=body).execute()


def update_task(
    list_id: str,
    task_id: str,
    title: str | None = None,
    notes: str | None = None,
    completed: bool | None = None,
) -> dict:
    service = get_tasks_service()
    body: dict = {}
    if title is not None:
        body["title"] = title
    if notes is not None:
        body["notes"] = notes
    if completed is not None:
        body["status"] = "completed" if completed else "needsAction"
    return service.tasks().patch(tasklist=list_id, task=task_id, body=body).execute()


def list_tasks(list_id: str) -> list[dict]:
    service = get_tasks_service()
    result = (
        service.tasks()
        .list(tasklist=list_id, showCompleted=True, showHidden=True, maxResults=100)
        .execute()
    )
    return result.get("items", [])
