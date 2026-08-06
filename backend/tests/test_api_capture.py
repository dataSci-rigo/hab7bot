import pytest
from fastapi.testclient import TestClient

from app.ai.schemas import CaptureInference


def test_capture_creates_task_using_ai_inference(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    role = auth_client.post("/api/v1/roles", json={"name": "Engineer"}).json()
    inference = CaptureInference(title="Call the accountant", role_name="Engineer", quadrant="Q1")
    monkeypatch.setattr("app.services.capture.infer_task_metadata", lambda db, text: inference)

    response = auth_client.post("/api/v1/capture", json={"text": "call the accountant re taxes"})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Call the accountant"
    assert body["role_id"] == role["id"]
    assert body["quadrant"] == "Q1"
    assert body["status"] == "inbox"


def test_capture_degrades_to_defaults_when_ai_unavailable(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    role = auth_client.post("/api/v1/roles", json={"name": "Engineer"}).json()
    monkeypatch.setattr("app.services.capture.infer_task_metadata", lambda db, text: None)

    response = auth_client.post("/api/v1/capture", json={"text": "buy milk"})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "buy milk"
    assert body["role_id"] == role["id"]
    assert body["quadrant"] == "Q2"
    assert body["status"] == "inbox"
