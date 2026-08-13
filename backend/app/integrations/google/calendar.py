"""Thin CRUD wrapper around the Google Calendar API v3. Sync logic lives in
sync.py."""
from datetime import date, datetime, timedelta

from app.integrations.google.auth import get_calendar_service

CALENDAR_NAME = "Compass"
DEFAULT_START_HOUR = 9  # tasks with an estimate but no specific time start here


def ensure_calendar() -> str:
    service = get_calendar_service()
    result = service.calendarList().list().execute()
    for cal in result.get("items", []):
        if cal.get("summary") == CALENDAR_NAME:
            return cal["id"]
    created = service.calendars().insert(body={"summary": CALENDAR_NAME}).execute()
    return created["id"]


def _event_body(
    title: str, notes: str | None, scheduled_day: date, estimate_minutes: int | None
) -> dict:
    body: dict = {"summary": title}
    if notes:
        body["description"] = notes
    if estimate_minutes:
        start = datetime.combine(scheduled_day, datetime.min.time()).replace(
            hour=DEFAULT_START_HOUR
        )
        end = start + timedelta(minutes=estimate_minutes)
        body["start"] = {"dateTime": start.isoformat()}
        body["end"] = {"dateTime": end.isoformat()}
    else:
        body["start"] = {"date": scheduled_day.isoformat()}
        body["end"] = {"date": (scheduled_day + timedelta(days=1)).isoformat()}
    return body


def insert_event(
    calendar_id: str,
    title: str,
    notes: str | None,
    scheduled_day: date,
    estimate_minutes: int | None,
) -> dict:
    service = get_calendar_service()
    body = _event_body(title, notes, scheduled_day, estimate_minutes)
    return service.events().insert(calendarId=calendar_id, body=body).execute()


def update_event(
    calendar_id: str,
    event_id: str,
    title: str,
    notes: str | None,
    scheduled_day: date,
    estimate_minutes: int | None,
) -> dict:
    service = get_calendar_service()
    body = _event_body(title, notes, scheduled_day, estimate_minutes)
    return service.events().patch(calendarId=calendar_id, eventId=event_id, body=body).execute()


def list_events(calendar_id: str) -> list[dict]:
    service = get_calendar_service()
    result = (
        service.events()
        .list(calendarId=calendar_id, maxResults=250, singleEvents=True, orderBy="startTime")
        .execute()
    )
    return result.get("items", [])
