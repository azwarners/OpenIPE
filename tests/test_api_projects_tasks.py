import asyncio

import httpx

from openipe.api.app import create_app
from openipe.persistence.database import initialize_database


class ApiTestClient:
    def __init__(self, app):
        self.app = app

    def request(self, method, path, **kwargs):
        async def send():
            transport = httpx.ASGITransport(app=self.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, path, **kwargs)
        return asyncio.run(send())

    def get(self, path, **kwargs): return self.request("GET", path, **kwargs)
    def post(self, path, **kwargs): return self.request("POST", path, **kwargs)
    def patch(self, path, **kwargs): return self.request("PATCH", path, **kwargs)


def authenticated_client(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    client = ApiTestClient(create_app(connection=connection))
    assert client.post("/api/v1/setup/initial-admin", json={"username": "admin", "display_name": "Admin", "password": "admin-pass"}).status_code == 201
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-pass"})
    return client, connection, {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_project_task_progress_and_next_action_api(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        project = client.post("/api/v1/projects", headers=headers, json={"title": "Build OpenIPE"})
        assert project.status_code == 201
        project_id = project.json()["id"]
        task = client.post("/api/v1/tasks", headers=headers, json={"title": "Implement API", "project_id": project_id, "priority": "high", "is_today": True})
        assert task.status_code == 201
        task_id = task.json()["id"]
        selected = client.post(f"/api/v1/projects/{project_id}/next-action/{task_id}", headers=headers)
        assert selected.status_code == 200
        assert selected.json()["next_action_task_id"] == task_id
        completed = client.post(f"/api/v1/tasks/{task_id}/complete", headers=headers)
        assert completed.status_code == 200
        detail = client.get(f"/api/v1/projects/{project_id}", headers=headers)
        assert detail.json()["completed_task_count"] == 1
        assert detail.json()["open_task_count"] == 0
        assert detail.json()["next_action_task_id"] is None
    finally:
        connection.close()


def test_inbox_conversion_endpoints_preserve_original(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        item = client.post("/api/v1/inbox", headers=headers, json={"text": "Ship the release"})
        item_id = item.json()["id"]
        project = client.post(f"/api/v1/inbox/{item_id}/create-project", headers=headers, json={})
        assert project.status_code == 201
        assert project.json()["source_inbox_item_id"] == item_id
        task = client.post(f"/api/v1/inbox/{item_id}/create-task", headers=headers, json={"project_id": project.json()["id"]})
        assert task.status_code == 201
        assert task.json()["source_inbox_item_id"] == item_id
        original = client.get(f"/api/v1/inbox/{item_id}", headers=headers)
        assert original.status_code == 200
        assert original.json()["status"] == "unprocessed"
    finally:
        connection.close()


def test_project_task_user_isolation_and_invalid_next_action(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        project = client.post("/api/v1/projects", headers=headers, json={"title": "Private project"})
        project_id = project.json()["id"]
        task = client.post("/api/v1/tasks", headers=headers, json={"title": "Private task"})
        task_id = task.json()["id"]
        assert client.post(f"/api/v1/projects/{project_id}/next-action/{task_id}", headers=headers).status_code == 400
        created = client.post("/api/v1/users", headers=headers, json={"username": "other", "display_name": "Other", "password": "other-pass"})
        other_login = client.post("/api/v1/auth/login", json={"username": "other", "password": "other-pass"})
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
        assert created.status_code == 201
        assert client.get("/api/v1/projects", headers=other_headers).json() == []
        assert client.get(f"/api/v1/tasks/{task_id}", headers=other_headers).status_code == 404
    finally:
        connection.close()
