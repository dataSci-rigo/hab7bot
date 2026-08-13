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


def test_settings_defaults_scheduled_job_times_then_updates(auth_client: TestClient) -> None:
    initial = auth_client.get("/api/v1/settings").json()
    assert initial["morning_brief_time"] == "07:30"
    assert initial["evening_checkin_time"] == "21:00"
    assert initial["weekly_review_time"] == "16:00"
    assert initial["weekly_planning_time"] == "17:00"

    updated = auth_client.put(
        "/api/v1/settings", json={"morning_brief_time": "08:00", "evening_checkin_time": "22:00"}
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["morning_brief_time"] == "08:00"
    assert body["evening_checkin_time"] == "22:00"
    # untouched fields unaffected by a partial update
    assert body["weekly_review_time"] == "16:00"
