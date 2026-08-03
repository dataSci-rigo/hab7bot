from fastapi.testclient import TestClient


def test_week_plan_splits_big_rocks_and_scheduled_tasks(auth_client: TestClient) -> None:
    role_id = auth_client.post("/api/v1/roles", json={"name": "Engineer"}).json()["id"]

    auth_client.post(
        "/api/v1/tasks",
        json={
            "title": "Big rock task",
            "role_id": role_id,
            "is_big_rock": True,
            "scheduled_week": "2026-W32",
        },
    )
    auth_client.post(
        "/api/v1/tasks",
        json={"title": "Regular task", "role_id": role_id, "scheduled_week": "2026-W32"},
    )
    auth_client.post(
        "/api/v1/tasks",
        json={"title": "Other week task", "role_id": role_id, "scheduled_week": "2026-W33"},
    )

    plan = auth_client.get("/api/v1/weeks/2026-W32/plan")
    assert plan.status_code == 200
    body = plan.json()
    assert body["iso_week"] == "2026-W32"
    assert [t["title"] for t in body["big_rocks"]] == ["Big rock task"]
    assert [t["title"] for t in body["scheduled_tasks"]] == ["Regular task"]


def test_set_role_intention(auth_client: TestClient) -> None:
    role_id = auth_client.post("/api/v1/roles", json={"name": "Health"}).json()["id"]

    response = auth_client.put(
        f"/api/v1/weeks/2026-W32/intentions/{role_id}", json={"note": "Rest and recover"}
    )
    assert response.status_code == 200

    plan = auth_client.get("/api/v1/weeks/2026-W32/plan").json()
    assert plan["role_intentions"] == [{"role_id": role_id, "note": "Rest and recover"}]
