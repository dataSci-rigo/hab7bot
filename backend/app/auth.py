import hmac
import logging
import re
from functools import lru_cache

from fastapi import HTTPException, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.config import settings

logger = logging.getLogger(__name__)

SESSION_COOKIE_NAME = "compass_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 days

ROLE_OWNER = "owner"
ROLE_GUEST = "guest"
ROLE_MEMBER = "member"

# Account names become part of a database filename (compass_acct_<name>.db),
# so this is a safety requirement, not cosmetics.
_ACCOUNT_NAME_RE = re.compile(r"^[a-z0-9_-]{1,32}$")

# Usernames claimed by the built-in logins (see api/v1/auth.py::login) —
# account entries with these names are skipped.
RESERVED_USERNAMES = {"owner", "demo"}

# Methods a guest session may use — guests are read-only across the whole
# API surface. Enforced centrally here (require_session is the dependency on
# every router) rather than per-route, so new routes are guest-safe by default.
_GUEST_ALLOWED_METHODS = {"GET", "HEAD", "OPTIONS"}

_serializer = URLSafeTimedSerializer(settings.session_secret, salt="compass-session")


@lru_cache(maxsize=1)
def parse_accounts() -> dict[str, str]:
    """HAB7BOT_ACCOUNTS ("name:password,name:password") → {name: password}.

    Login takes username + password, so the username disambiguates — but
    matching passwords across logins (including APP_PASSWORD and
    DEMO_PASSWORD) are still warned about loudly: a shared password means one
    person can trivially log into another's planner by guessing the username.
    Cached: settings are process-lifetime constants (tests clear the cache).
    """
    accounts: dict[str, str] = {}
    seen_passwords = {settings.app_password: "owner", settings.demo_password: "demo"}
    for entry in settings.accounts.split(","):
        entry = entry.strip()
        if not entry:
            continue
        name, sep, password = entry.partition(":")
        name = name.strip()
        if not sep or not password or not _ACCOUNT_NAME_RE.match(name):
            logger.warning("Skipping malformed account entry %r", entry.split(":")[0])
            continue
        if name in RESERVED_USERNAMES:
            logger.warning("Skipping account %r — reserved username", name)
            continue
        if password in seen_passwords:
            logger.warning(
                "PASSWORD COLLISION: account %r has the same password as %r — "
                "either login can access the other's planner by switching "
                "usernames. Give every login a unique password.",
                name, seen_passwords[password],
            )
        seen_passwords.setdefault(password, name)
        accounts[name] = password
    return accounts


def make_session_token(role: str = ROLE_OWNER, account: str | None = None) -> str:
    payload: dict = {"authenticated": True, "role": role}
    if account is not None:
        payload["account"] = account
    return _serializer.dumps(payload)


def _session_payload(token: str) -> dict | None:
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except BadSignature:
        return None
    return data if data.get("authenticated") else None


def session_role(token: str) -> str | None:
    """Role for a valid session token, or None if invalid/expired.

    Tokens minted before roles existed carry no "role" key — treat them as
    owner so the user's existing 30-day cookie keeps working.
    """
    data = _session_payload(token)
    return data.get("role", ROLE_OWNER) if data else None


def request_session_identity(request: Request) -> tuple[str, str | None] | None:
    """(role, account_name) for the request's session, or None.

    account_name is set only for member sessions, and only if the account
    still exists in settings — a member whose account was removed from
    HAB7BOT_ACCOUNTS is treated as unauthenticated rather than silently
    falling through to some other database.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    data = _session_payload(token)
    if data is None:
        return None
    role = data.get("role", ROLE_OWNER)
    if role == ROLE_MEMBER:
        account = data.get("account")
        if not account or account not in parse_accounts():
            return None
        return (role, account)
    return (role, None)


def request_session_role(request: Request) -> str | None:
    identity = request_session_identity(request)
    return identity[0] if identity else None


def require_session(request: Request) -> None:
    role = request_session_role(request)
    if role is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if role == ROLE_GUEST and request.method not in _GUEST_ALLOWED_METHODS:
        raise HTTPException(status_code=403, detail="Guest access is read-only")


def require_owner(request: Request) -> None:
    """Owner-only routes — currently /google/*: the Google OAuth token is the
    owner's, so members/guests must never trigger syncs against it."""
    role = request_session_role(request)
    if role is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if role != ROLE_OWNER:
        raise HTTPException(status_code=403, detail="Owner only")


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
