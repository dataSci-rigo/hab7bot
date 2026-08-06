import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai.schemas import BreakdownProposal, ProjectSuggestionsOutput

FIXTURES = Path(__file__).parent / "fixtures" / "ai"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture()
def project_and_role(auth_client: TestClient):
    role = auth_client.post("/api/v1/roles", json={"name": "Engineer"}).json()
    project = auth_client.post(
        "/api/v1/projects", json={"role_id": role["id"], "title": "Migrate to Postgres"}
    ).json()
    return role, project


def test_breakdown_returns_proposal_without_writing_tasks(
    auth_client: TestClient, project_and_role, monkeypatch: pytest.MonkeyPatch
) -> None:
    _role, project = project_and_role
    fixture = BreakdownProposal.model_validate(_load("breakdown.json"))
    monkeypatch.setattr("app.api.v1.projects.ai_breakdown_project", lambda db, pid: fixture)

    response = auth_client.post(f"/api/v1/projects/{project['id']}/breakdown")
    assert response.status_code == 200
    body = response.json()
    assert len(body["milestones"]) == len(fixture.milestones)

    # nothing written yet
    tasks = auth_client.get("/api/v1/tasks", params={"project_id": project["id"]}).json()
    assert tasks == []


def test_breakdown_accept_creates_tasks(
    auth_client: TestClient, project_and_role
) -> None:
    _role, project = project_and_role
    selected = [
        {"title": "Audit schema", "quadrant": "Q2", "estimate_minutes": 60},
        {"title": "Provision Postgres", "quadrant": "Q2", "suggested_week_offset": 1},
    ]
    response = auth_client.post(
        f"/api/v1/projects/{project['id']}/breakdown/accept", json={"selected": selected}
    )
    assert response.status_code == 201
    created = response.json()
    assert len(created) == 2
    assert {t["title"] for t in created} == {"Audit schema", "Provision Postgres"}
    assert all(t["project_id"] == project["id"] for t in created)
    assert all(t["origin"] == "ai" for t in created)


def test_breakdown_returns_503_when_ai_unavailable(
    auth_client: TestClient, project_and_role, monkeypatch: pytest.MonkeyPatch
) -> None:
    _role, project = project_and_role
    monkeypatch.setattr("app.api.v1.projects.ai_breakdown_project", lambda db, pid: None)

    response = auth_client.post(f"/api/v1/projects/{project['id']}/breakdown")
    assert response.status_code == 503


def test_suggestions_returns_list_without_writing_projects(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = ProjectSuggestionsOutput.model_validate(_load("suggestions.json"))
    monkeypatch.setattr("app.api.v1.projects.ai_suggest_projects", lambda db: fixture)

    response = auth_client.post("/api/v1/projects/suggestions")
    assert response.status_code == 200
    assert len(response.json()) == len(fixture.suggestions)

    assert auth_client.get("/api/v1/projects").json() == []


def test_suggestions_accept_creates_project(
    auth_client: TestClient, project_and_role
) -> None:
    role, _existing_project = project_and_role
    suggestion = {
        "title": "Half Marathon Training Plan",
        "role_name": role["name"],
        "rationale": "Bridges the gap between the goal and daily action.",
        "first_three_tasks": ["Pick a race", "Pick a plan", "Schedule runs"],
        "quadrant_profile": "Not Urgent & Important",
    }
    response = auth_client.post(
        "/api/v1/projects/suggestions/accept", json={"suggestion": suggestion}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Half Marathon Training Plan"
    assert body["status"] == "idea"
    assert body["origin"] == "ai"


def test_suggestions_returns_503_when_ai_unavailable(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.v1.projects.ai_suggest_projects", lambda db: None)
    response = auth_client.post("/api/v1/projects/suggestions")
    assert response.status_code == 503
