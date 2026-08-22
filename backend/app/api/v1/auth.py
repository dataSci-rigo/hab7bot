import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from app.auth import (
    ROLE_GUEST,
    ROLE_OWNER,
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    make_session_token,
    request_session_role,
    require_session,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


def _matches(candidate: str, expected: str) -> bool:
    # encode: compare_digest on str raises TypeError for non-ASCII input
    return bool(expected) and hmac.compare_digest(candidate.encode(), expected.encode())


def _set_session_cookie(response: Response, role: str) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        make_session_token(role),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
    )


@router.post("/login")
def login(data: LoginRequest, response: Response) -> dict[str, bool | str]:
    """One form, two passwords: the owner's APP_PASSWORD, or the openly
    hinted demo password ("demo" by default) which starts a read-only
    session served from the seeded showcase database (scripts/seed_demo.py)
    — never the real planner. Owner match is checked first so the demo
    password can never shadow it."""
    if _matches(data.password, settings.app_password):
        role = ROLE_OWNER
    elif _matches(data.password, settings.demo_password):
        role = ROLE_GUEST
    else:
        raise HTTPException(status_code=401, detail="Incorrect password")
    _set_session_cookie(response, role)
    return {"ok": True, "role": role}


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"ok": True}


@router.get("/me", dependencies=[Depends(require_session)])
def me(request: Request) -> dict[str, bool | str]:
    return {"authenticated": True, "role": request_session_role(request) or ROLE_OWNER}
