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
    assert client.get("/api/v1/auth/me").json() == {"authenticated": True}
