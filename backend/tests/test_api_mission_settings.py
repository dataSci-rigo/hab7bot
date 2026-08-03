from fastapi.testclient import TestClient


def test_mission_defaults_empty_then_updates(auth_client: TestClient) -> None:
    initial = auth_client.get("/api/v1/mission")
    assert initial.status_code == 200
    assert initial.json()["content"] == ""

    updated = auth_client.put("/api/v1/mission", json={"content": "Be present. Build well."})
    assert updated.status_code == 200
    assert updated.json()["content"] == "Be present. Build well."

    refetched = auth_client.get("/api/v1/mission")
    assert refetched.json()["content"] == "Be present. Build well."


def test_settings_defaults_monday_then_updates(auth_client: TestClient) -> None:
    initial = auth_client.get("/api/v1/settings")
    assert initial.status_code == 200
    assert initial.json()["week_start_day"] == "monday"

    updated = auth_client.put("/api/v1/settings", json={"week_start_day": "sunday"})
    assert updated.status_code == 200
    assert updated.json()["week_start_day"] == "sunday"
