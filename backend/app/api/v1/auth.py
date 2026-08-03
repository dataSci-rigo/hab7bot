from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from app.auth import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    make_session_token,
    require_session,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
def login(data: LoginRequest, response: Response) -> dict[str, bool]:
    if data.password != settings.app_password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    response.set_cookie(
        SESSION_COOKIE_NAME,
        make_session_token(),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return {"ok": True}


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"ok": True}


@router.get("/me", dependencies=[Depends(require_session)])
def me() -> dict[str, bool]:
    return {"authenticated": True}
