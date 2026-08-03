from fastapi.testclient import TestClient


def test_create_list_update_delete_role(auth_client: TestClient) -> None:
    create = auth_client.post("/api/v1/roles", json={"name": "Parent"})
    assert create.status_code == 201
    role_id = create.json()["id"]

    listed = auth_client.get("/api/v1/roles")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = auth_client.put(f"/api/v1/roles/{role_id}", json={"description": "family stuff"})
    assert updated.status_code == 200
    assert updated.json()["description"] == "family stuff"

    deleted = auth_client.delete(f"/api/v1/roles/{role_id}")
    assert deleted.status_code == 204

    assert auth_client.get(f"/api/v1/roles/{role_id}").status_code == 404


def test_get_missing_role_404(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/roles/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
