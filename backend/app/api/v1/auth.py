import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from app.auth import (
    ROLE_GUEST,
    ROLE_MEMBER,
    ROLE_OWNER,
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    make_session_token,
    parse_accounts,
    request_session_identity,
    require_session,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


def _matches(candidate: str, expected: str) -> bool:
    # encode: compare_digest on str raises TypeError for non-ASCII input
    return bool(expected) and hmac.compare_digest(candidate.encode(), expected.encode())


def _set_session_cookie(response: Response, role: str, account: str | None = None) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        make_session_token(role, account),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
    )


@router.post("/login")
def login(data: LoginRequest, response: Response) -> dict[str, bool | str]:
    """One form, one password box — the password IS the identity:
    APP_PASSWORD → owner (real planner); the openly hinted demo password →
    read-only guest served from the seeded showcase DB; an HAB7BOT_ACCOUNTS
    password → that member's own private database. Owner is matched first so
    nothing can shadow it; parse_accounts warns about duplicate passwords."""
    role: str | None = None
    account: str | None = None
    if _matches(data.password, settings.app_password):
        role = ROLE_OWNER
    elif _matches(data.password, settings.demo_password):
        role = ROLE_GUEST
    else:
        for name, password in parse_accounts().items():
            if _matches(data.password, password):
                role, account = ROLE_MEMBER, name
                break
    if role is None:
        raise HTTPException(status_code=401, detail="Incorrect password")
    _set_session_cookie(response, role, account)
    result: dict[str, bool | str] = {"ok": True, "role": role}
    if account is not None:
        result["account"] = account
    return result


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"ok": True}


@router.get("/me", dependencies=[Depends(require_session)])
def me(request: Request) -> dict[str, bool | str]:
    identity = request_session_identity(request)
    role, account = identity if identity else (ROLE_OWNER, None)
    result: dict[str, bool | str] = {"authenticated": True, "role": role}
    if account is not None:
        result["account"] = account
    return result
