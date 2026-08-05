import asyncio

import httpx

from openipe.api.app import create_app
from openipe.persistence.database import initialize_database


class ApiTestClient:
    def __init__(self, app): self.app = app
    def request(self, method, path, **kwargs):
        async def send():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test") as client:
                return await client.request(method, path, **kwargs)
        return asyncio.run(send())
    def get(self, path, **kwargs): return self.request("GET", path, **kwargs)
    def post(self, path, **kwargs): return self.request("POST", path, **kwargs)
    def delete(self, path, **kwargs): return self.request("DELETE", path, **kwargs)


def authenticated_client(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    client = ApiTestClient(create_app(connection=connection))
    assert client.post("/api/v1/setup/initial-admin", json={"username": "admin", "display_name": "Admin", "password": "admin-pass"}).status_code == 201
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-pass"})
    return client, connection, {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_goal_association_endpoints_and_evidence_response(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        goal = client.post("/api/v1/goals", headers=headers, json={"title": "Publish"})
        project = client.post("/api/v1/projects", headers=headers, json={"title": "Project"})
        task = client.post("/api/v1/tasks", headers=headers, json={"title": "Task"})
        habit = client.post("/api/v1/habits", headers=headers, json={"title": "Habit"})
        goal_id = goal.json()["id"]
        project_id, task_id, habit_id = project.json()["id"], task.json()["id"], habit.json()["id"]
        assert client.post(f"/api/v1/goals/{goal_id}/projects/{project_id}", headers=headers).status_code == 200
        assert client.post(f"/api/v1/goals/{goal_id}/tasks/{task_id}", headers=headers).status_code == 200
        assert client.post(f"/api/v1/goals/{goal_id}/habits/{habit_id}", headers=headers).status_code == 200
        detail = client.get(f"/api/v1/goals/{goal_id}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["project_ids"] == [project_id]
        assert detail.json()["task_ids"] == [task_id]
        assert detail.json()["habit_ids"] == [habit_id]
        assert detail.json()["evidence"]["tasks_open"] == 1
        assert client.delete(f"/api/v1/goals/{goal_id}/tasks/{task_id}", headers=headers).status_code == 204
        assert client.get(f"/api/v1/goals/{goal_id}", headers=headers).json()["task_ids"] == []
    finally:
        connection.close()


def test_cross_user_association_is_rejected(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        goal = client.post("/api/v1/goals", headers=headers, json={"title": "Private goal"})
        other = client.post("/api/v1/users", headers=headers, json={"username": "other", "display_name": "Other", "password": "other-pass"})
        login = client.post("/api/v1/auth/login", json={"username": "other", "password": "other-pass"})
        other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        project = client.post("/api/v1/projects", headers=other_headers, json={"title": "Other project"})
        assert other.status_code == 201
        assert client.post(f"/api/v1/goals/{goal.json()['id']}/projects/{project.json()['id']}", headers=headers).status_code == 404
    finally:
        connection.close()
