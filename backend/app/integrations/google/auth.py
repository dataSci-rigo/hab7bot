"""OAuth credential loading/refresh — mirrors semantic_task_manager's
google_tasks.py pattern. Requires a one-time local authorization via
scripts/google_oauth_setup.py before use (see that script for why it can't
run headlessly or on the VM)."""
import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/calendar",
]

_tasks_service: Resource | None = None
_calendar_service: Resource | None = None


class GoogleAuthError(Exception):
    """Raised when there's no valid token yet — callers should degrade
    gracefully (skip sync) rather than crash, same posture as AI failures."""


def _load_credentials() -> Credentials:
    token_path = Path(settings.google_token_path)
    if not token_path.exists():
        raise GoogleAuthError(
            f"No Google token at {token_path} — run "
            "`python -m scripts.google_oauth_setup` once, locally, to authorize."
        )
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json())
    return creds


def is_authorized() -> bool:
    return Path(settings.google_token_path).exists()


def get_tasks_service() -> Resource:
    global _tasks_service
    if _tasks_service is None:
        _tasks_service = build("tasks", "v1", credentials=_load_credentials())
    return _tasks_service


def get_calendar_service() -> Resource:
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = build("calendar", "v3", credentials=_load_credentials())
    return _calendar_service
