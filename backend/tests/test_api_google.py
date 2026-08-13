import pytest
from fastapi.testclient import TestClient


def test_status_not_connected_when_no_token(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.v1.google.is_authorized", lambda: False)
    response = auth_client.get("/api/v1/google/status")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert body["last_synced_at"] is None


def test_status_connected_reports_last_synced(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.v1.google.is_authorized", lambda: True)
    response = auth_client.get("/api/v1/google/status")
    assert response.status_code == 200
    assert response.json()["connected"] is True


def test_sync_endpoint_returns_result(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_result = {
        "ok": True,
        "tasks": {"pushed_created": 1, "pushed_updated": 0, "pulled": 0},
        "calendar": {"pushed_created": 0, "pushed_updated": 0, "pulled": 0},
    }
    monkeypatch.setattr("app.api.v1.google.sync_all", lambda db: fake_result)

    response = auth_client.post("/api/v1/google/sync")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["tasks"]["pushed_created"] == 1


def test_sync_endpoint_reports_degradation(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.api.v1.google.sync_all", lambda db: {"ok": False, "reason": "not authorized"}
    )

    response = auth_client.post("/api/v1/google/sync")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["reason"] == "not authorized"
