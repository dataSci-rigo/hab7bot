import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.google_link import GoogleCalendarEventLink, GoogleTaskLink


def now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def last_synced_at(db: Session) -> datetime | None:
    """Most recent sync across both link tables, or None if nothing has
    synced yet — used for GET /google/status."""
    task_max = db.scalar(select(GoogleTaskLink.last_synced_at).order_by(
        GoogleTaskLink.last_synced_at.desc()
    ).limit(1))
    event_max = db.scalar(select(GoogleCalendarEventLink.last_synced_at).order_by(
        GoogleCalendarEventLink.last_synced_at.desc()
    ).limit(1))
    candidates = [t for t in (task_max, event_max) if t is not None]
    return max(candidates) if candidates else None


# ── task links ───────────────────────────────────────────────────────────────


def get_task_link(db: Session, task_id: uuid.UUID) -> GoogleTaskLink | None:
    return db.scalar(select(GoogleTaskLink).where(GoogleTaskLink.task_id == task_id))


def get_task_link_by_google_id(db: Session, google_task_id: str) -> GoogleTaskLink | None:
    return db.scalar(
        select(GoogleTaskLink).where(GoogleTaskLink.google_task_id == google_task_id)
    )


def list_task_links(db: Session) -> list[GoogleTaskLink]:
    return list(db.scalars(select(GoogleTaskLink)))


def create_task_link(
    db: Session,
    task_id: uuid.UUID,
    google_task_id: str,
    google_list_id: str,
    google_updated_at: str | None,
) -> GoogleTaskLink:
    link = GoogleTaskLink(
        task_id=task_id,
        google_task_id=google_task_id,
        google_list_id=google_list_id,
        google_updated_at=google_updated_at,
        last_synced_at=now(),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def touch_task_link(
    db: Session, link: GoogleTaskLink, google_updated_at: str | None
) -> GoogleTaskLink:
    link.google_updated_at = google_updated_at
    link.last_synced_at = now()
    db.commit()
    db.refresh(link)
    return link


# ── calendar event links ────────────────────────────────────────────────────


def get_event_link(db: Session, task_id: uuid.UUID) -> GoogleCalendarEventLink | None:
    return db.scalar(
        select(GoogleCalendarEventLink).where(GoogleCalendarEventLink.task_id == task_id)
    )


def get_event_link_by_google_id(
    db: Session, google_event_id: str
) -> GoogleCalendarEventLink | None:
    return db.scalar(
        select(GoogleCalendarEventLink).where(
            GoogleCalendarEventLink.google_event_id == google_event_id
        )
    )


def list_event_links(db: Session) -> list[GoogleCalendarEventLink]:
    return list(db.scalars(select(GoogleCalendarEventLink)))


def create_event_link(
    db: Session,
    task_id: uuid.UUID,
    google_event_id: str,
    google_calendar_id: str,
    google_updated_at: str | None,
) -> GoogleCalendarEventLink:
    link = GoogleCalendarEventLink(
        task_id=task_id,
        google_event_id=google_event_id,
        google_calendar_id=google_calendar_id,
        google_updated_at=google_updated_at,
        last_synced_at=now(),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def touch_event_link(
    db: Session, link: GoogleCalendarEventLink, google_updated_at: str | None
) -> GoogleCalendarEventLink:
    link.google_updated_at = google_updated_at
    link.last_synced_at = now()
    db.commit()
    db.refresh(link)
    return link
