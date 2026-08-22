import hmac

from fastapi import HTTPException, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.config import settings

SESSION_COOKIE_NAME = "compass_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 days

ROLE_OWNER = "owner"
ROLE_GUEST = "guest"

# Methods a guest session may use — guests are read-only across the whole
# API surface. Enforced centrally here (require_session is the dependency on
# every router) rather than per-route, so new routes are guest-safe by default.
_GUEST_ALLOWED_METHODS = {"GET", "HEAD", "OPTIONS"}

_serializer = URLSafeTimedSerializer(settings.session_secret, salt="compass-session")


def make_session_token(role: str = ROLE_OWNER) -> str:
    return _serializer.dumps({"authenticated": True, "role": role})


def session_role(token: str) -> str | None:
    """Role for a valid session token, or None if invalid/expired.

    Tokens minted before roles existed carry no "role" key — treat them as
    owner so the user's existing 30-day cookie keeps working.
    """
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except BadSignature:
        return None
    if not data.get("authenticated"):
        return None
    return data.get("role", ROLE_OWNER)


def request_session_role(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return session_role(token) if token else None


def require_session(request: Request) -> None:
    role = request_session_role(request)
    if role is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if role == ROLE_GUEST and request.method not in _GUEST_ALLOWED_METHODS:
        raise HTTPException(status_code=403, detail="Guest access is read-only")


def require_session_or_api_key(request: Request) -> None:
    """Session cookie, or the internal X-Api-Key used by trusted local bots
    (brain-dump). The key path stays disabled until HAB7BOT_INTERNAL_API_KEY
    is set."""
    key = request.headers.get("X-Api-Key")
    if key and settings.internal_api_key and hmac.compare_digest(
        key, settings.internal_api_key
    ):
        return
    require_session(request)
