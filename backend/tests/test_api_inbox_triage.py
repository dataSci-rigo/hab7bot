import pytest
from fastapi.testclient import TestClient

from app.ai.schemas import InboxTriageItem, InboxTriageOutput


def test_ai_triage_resolves_role_and_project(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    role = auth_client.post("/api/v1/roles", json={"name": "Engineer"}).json()
    project = auth_client.post(
        "/api/v1/projects", json={"role_id": role["id"], "title": "Migrate to Postgres"}
    ).json()
    task = auth_client.post(
        "/api/v1/tasks", json={"title": "write migration script", "role_id": role["id"]}
    ).json()

    fixture = InboxTriageOutput(
        items=[
            InboxTriageItem(
                task_id=task["id"],
                role_name="Engineer",
                quadrant="Q2",
                is_big_rock_candidate=True,
                project_title_match="Migrate to Postgres",
            )
        ]
    )
    monkeypatch.setattr("app.services.inbox_triage.triage_inbox", lambda db: fixture)

    response = auth_client.post("/api/v1/inbox/ai-triage")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["task_id"] == task["id"]
    assert body[0]["role_id"] == role["id"]
    assert body[0]["project_id"] == project["id"]
    assert body[0]["is_big_rock_candidate"] is True


def test_ai_triage_returns_503_when_ai_unavailable(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.services.inbox_triage.triage_inbox", lambda db: None)
    response = auth_client.post("/api/v1/inbox/ai-triage")
    assert response.status_code == 503
