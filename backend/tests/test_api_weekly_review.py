import pytest
from fastapi.testclient import TestClient


def test_get_review_404_when_not_generated(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/weeks/2026-W33/review")
    assert response.status_code == 404


def test_generate_review_creates_and_returns_it(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "app.services.weekly_review.analyze_week",
        lambda stats, previous, reflection: None,
    )

    response = auth_client.post("/api/v1/weeks/2026-W33/review/generate")
    assert response.status_code == 200
    body = response.json()
    assert body["iso_week"] == "2026-W33"
    assert body["stats"] is not None

    fetched = auth_client.get("/api/v1/weeks/2026-W33/review")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


def test_generate_review_is_idempotent_via_api(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []
    monkeypatch.setattr(
        "app.services.weekly_review.analyze_week",
        lambda stats, previous, reflection: calls.append(1) or None,
    )

    auth_client.post("/api/v1/weeks/2026-W33/review/generate")
    auth_client.post("/api/v1/weeks/2026-W33/review/generate")
    assert len(calls) == 1

    auth_client.post("/api/v1/weeks/2026-W33/review/generate", params={"force": True})
    assert len(calls) == 2


def test_set_reflection_via_api(auth_client: TestClient) -> None:
    response = auth_client.put(
        "/api/v1/weeks/2026-W33/review/reflection", json={"reflection": "Went well."}
    )
    assert response.status_code == 200
    assert response.json()["reflection"] == "Went well."


def test_review_routes_require_auth(client: TestClient) -> None:
    response = client.get("/api/v1/weeks/2026-W33/review")
    assert response.status_code == 401
