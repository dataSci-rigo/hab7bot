from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import settings


def test_unauthenticated_request_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/roles")
    assert response.status_code == 401


def test_login_wrong_password_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/auth/login", json={"password": "wrong"})
    assert response.status_code == 401


def test_login_then_authenticated_request_succeeds(client: TestClient) -> None:
    login = client.post("/api/v1/auth/login", json={"password": settings.app_password})
    assert login.status_code == 200

    response = client.get("/api/v1/roles")
    assert response.status_code == 200
    assert response.json() == []


def test_logout_clears_session(auth_client: TestClient) -> None:
    assert auth_client.get("/api/v1/roles").status_code == 200
    auth_client.post("/api/v1/auth/logout")
    assert auth_client.get("/api/v1/roles").status_code == 401


def test_me_reflects_session_state(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401
    client.post("/api/v1/auth/login", json={"password": settings.app_password})
    assert client.get("/api/v1/auth/me").json() == {"authenticated": True, "role": "owner"}


# ── demo (guest) sessions ───────────────────────────────────────────────────


def test_empty_password_never_logs_in(client: TestClient, monkeypatch) -> None:
    # even if APP_PASSWORD were accidentally blanked, "" must not match ""
    monkeypatch.setattr(settings, "app_password", "")
    assert client.post("/api/v1/auth/login", json={"password": ""}).status_code == 401


def test_demo_password_sets_guest_role(client: TestClient) -> None:
    demo = client.post("/api/v1/auth/login", json={"password": "demo"})
    assert demo.status_code == 200
    assert demo.json() == {"ok": True, "role": "guest"}
    assert client.get("/api/v1/auth/me").json() == {"authenticated": True, "role": "guest"}


def test_demo_session_can_read_but_not_write(client: TestClient) -> None:
    client.post("/api/v1/auth/login", json={"password": "demo"})

    assert client.get("/api/v1/roles").status_code == 200
    assert client.post("/api/v1/roles", json={"name": "Sneaky"}).status_code == 403
    assert client.put("/api/v1/settings", json={"week_start_day": "sunday"}).status_code == 403
    # AI/sync triggers are POSTs — blocked too (they cost money / mutate)
    assert client.post("/api/v1/google/sync").status_code == 403


def test_demo_session_can_log_out(client: TestClient) -> None:
    client.post("/api/v1/auth/login", json={"password": "demo"})
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/roles").status_code == 401


def test_owner_password_still_grants_full_access(client: TestClient) -> None:
    login = client.post("/api/v1/auth/login", json={"password": settings.app_password})
    assert login.json() == {"ok": True, "role": "owner"}
    assert client.post("/api/v1/roles", json={"name": "Engineer"}).status_code == 201


def test_pre_role_session_token_still_works_as_owner(client: TestClient) -> None:
    """Cookies minted before roles existed have no "role" key — they must
    keep working as owner sessions (30-day cookies in the wild)."""
    from app.auth import SESSION_COOKIE_NAME, _serializer

    old_token = _serializer.dumps({"authenticated": True})
    client.cookies.set(SESSION_COOKIE_NAME, old_token)

    assert client.get("/api/v1/roles").status_code == 200
    assert client.post("/api/v1/roles", json={"name": "Engineer"}).status_code == 201


def test_get_db_routes_guest_to_demo_session(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import Request

    from app import db as db_module
    from app.auth import ROLE_GUEST, SESSION_COOKIE_NAME, make_session_token

    demo_session = MagicMock(name="demo_session")
    monkeypatch.setattr(db_module, "_demo_session", lambda: demo_session)

    def request_with(token: str | None) -> Request:
        headers = []
        if token is not None:
            headers.append((b"cookie", f"{SESSION_COOKIE_NAME}={token}".encode()))
        return Request(
            {"type": "http", "method": "GET", "path": "/", "query_string": b"",
             "headers": headers}
        )

    # guest cookie → demo session
    gen = db_module.get_db(request_with(make_session_token(ROLE_GUEST)))
    assert next(gen) is demo_session
    gen.close()
    demo_session.close.assert_called_once()

    # owner cookie → the real SessionLocal, not the demo one
    gen = db_module.get_db(request_with(make_session_token()))
    owner_db = next(gen)
    assert owner_db is not demo_session
    gen.close()
