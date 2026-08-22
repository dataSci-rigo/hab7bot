from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import settings


def test_unauthenticated_request_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/roles")
    assert response.status_code == 401


def test_login_wrong_password_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/auth/login", json={"username": "owner", "password": "wrong"})
    assert response.status_code == 401


def test_login_then_authenticated_request_succeeds(client: TestClient) -> None:
    login = client.post(
        "/api/v1/auth/login", json={"username": "owner", "password": settings.app_password}
    )
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
    client.post(
        "/api/v1/auth/login", json={"username": "owner", "password": settings.app_password}
    )
    assert client.get("/api/v1/auth/me").json() == {"authenticated": True, "role": "owner"}


# ── demo (guest) sessions ───────────────────────────────────────────────────


def test_empty_password_never_logs_in(client: TestClient, monkeypatch) -> None:
    # even if APP_PASSWORD were accidentally blanked, "" must not match ""
    monkeypatch.setattr(settings, "app_password", "")
    response = client.post("/api/v1/auth/login", json={"username": "owner", "password": ""})
    assert response.status_code == 401


def test_demo_password_sets_guest_role(client: TestClient) -> None:
    demo = client.post("/api/v1/auth/login", json={"username": "demo", "password": "demo"})
    assert demo.status_code == 200
    assert demo.json() == {"ok": True, "role": "guest"}
    assert client.get("/api/v1/auth/me").json() == {"authenticated": True, "role": "guest"}


def test_demo_session_can_read_but_not_write(client: TestClient) -> None:
    client.post("/api/v1/auth/login", json={"username": "demo", "password": "demo"})

    assert client.get("/api/v1/roles").status_code == 200
    assert client.post("/api/v1/roles", json={"name": "Sneaky"}).status_code == 403
    assert client.put("/api/v1/settings", json={"week_start_day": "sunday"}).status_code == 403
    # AI/sync triggers are POSTs — blocked too (they cost money / mutate)
    assert client.post("/api/v1/google/sync").status_code == 403


def test_demo_session_can_log_out(client: TestClient) -> None:
    client.post("/api/v1/auth/login", json={"username": "demo", "password": "demo"})
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/roles").status_code == 401


def test_owner_password_still_grants_full_access(client: TestClient) -> None:
    login = client.post(
        "/api/v1/auth/login", json={"username": "owner", "password": settings.app_password}
    )
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


# ── member accounts ─────────────────────────────────────────────────────────


@pytest.fixture()
def accounts(monkeypatch: pytest.MonkeyPatch):
    from app.auth import parse_accounts

    monkeypatch.setattr(settings, "accounts", "ana:pw-ana,leo:pw-leo")
    parse_accounts.cache_clear()
    yield
    parse_accounts.cache_clear()


def test_parse_accounts_skips_malformed_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.auth import parse_accounts

    monkeypatch.setattr(
        settings, "accounts",
        "ok_name:pw1, Bad Name:pw2 ,nopassword, UPPER:pw3," + "x" * 40 + ":pw4,also-ok:pw5",
    )
    parse_accounts.cache_clear()
    try:
        assert parse_accounts() == {"ok_name": "pw1", "also-ok": "pw5"}
    finally:
        parse_accounts.cache_clear()


def test_right_password_wrong_username_rejected(client: TestClient, accounts) -> None:
    # username disambiguates — a valid password under the wrong name fails
    assert client.post(
        "/api/v1/auth/login", json={"username": "leo", "password": "pw-ana"}
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login", json={"username": "owner", "password": "pw-ana"}
    ).status_code == 401


def test_parse_accounts_reserved_names_and_password_collisions(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from app.auth import parse_accounts

    # "owner" is reserved; "ana" reuses the demo password ("demo" default)
    monkeypatch.setattr(settings, "accounts", "owner:sneak,ana:demo,leo:pw-leo")
    parse_accounts.cache_clear()
    try:
        with caplog.at_level("WARNING"):
            parsed = parse_accounts()
    finally:
        parse_accounts.cache_clear()

    assert parsed == {"ana": "demo", "leo": "pw-leo"}
    assert any("reserved" in r.message for r in caplog.records)
    assert any("PASSWORD COLLISION" in r.message for r in caplog.records)


def test_member_login_and_me(client: TestClient, accounts) -> None:
    login = client.post("/api/v1/auth/login", json={"username": "ana", "password": "pw-ana"})
    assert login.status_code == 200
    assert login.json() == {"ok": True, "role": "member", "account": "ana"}
    assert client.get("/api/v1/auth/me").json() == {
        "authenticated": True, "role": "member", "account": "ana",
    }


def test_member_can_write_unlike_guest(client: TestClient, accounts) -> None:
    client.post("/api/v1/auth/login", json={"username": "leo", "password": "pw-leo"})
    assert client.post("/api/v1/roles", json={"name": "Engineer"}).status_code == 201


def test_member_session_dies_when_account_removed(client: TestClient, accounts) -> None:
    from app.auth import parse_accounts

    client.post("/api/v1/auth/login", json={"username": "ana", "password": "pw-ana"})
    assert client.get("/api/v1/auth/me").status_code == 200

    # account deleted from HAB7BOT_ACCOUNTS → existing cookie must go dead,
    # not silently fall through to some other database
    settings.accounts = "leo:pw-leo"
    parse_accounts.cache_clear()
    assert client.get("/api/v1/auth/me").status_code == 401


def test_google_routes_are_owner_only(
    client: TestClient, accounts, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.v1.google.is_authorized", lambda: False)

    client.post("/api/v1/auth/login", json={"username": "ana", "password": "pw-ana"})
    assert client.get("/api/v1/google/status").status_code == 403

    client.post("/api/v1/auth/login", json={"username": "demo", "password": "demo"})
    assert client.get("/api/v1/google/status").status_code == 403

    client.post(
        "/api/v1/auth/login", json={"username": "owner", "password": settings.app_password}
    )
    assert client.get("/api/v1/google/status").status_code == 200


def test_get_db_routes_members_to_their_own_db(
    accounts, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fastapi import Request

    from app import db as db_module
    from app.auth import ROLE_MEMBER, SESSION_COOKIE_NAME, make_session_token

    opened: list[str] = []

    def fake_account_session(name: str):
        opened.append(name)
        return MagicMock(name=f"session-{name}")

    monkeypatch.setattr(db_module, "_account_session", fake_account_session)

    def request_for(account: str) -> Request:
        token = make_session_token(ROLE_MEMBER, account)
        return Request(
            {"type": "http", "method": "GET", "path": "/", "query_string": b"",
             "headers": [(b"cookie", f"{SESSION_COOKIE_NAME}={token}".encode())]}
        )

    for name in ("ana", "leo"):
        gen = db_module.get_db(request_for(name))
        next(gen)
        gen.close()
    assert opened == ["ana", "leo"]

    # distinct DB files per account
    assert db_module.account_database_url("ana") != db_module.account_database_url("leo")
    assert "compass_acct_ana.db" in db_module.account_database_url("ana")


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
