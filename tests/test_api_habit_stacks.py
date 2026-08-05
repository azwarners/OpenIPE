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
    def patch(self, path, **kwargs): return self.request("PATCH", path, **kwargs)
    def delete(self, path, **kwargs): return self.request("DELETE", path, **kwargs)


def authenticated_client(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    client = ApiTestClient(create_app(connection=connection))
    assert client.post("/api/v1/setup/initial-admin", json={"username": "admin", "display_name": "Admin", "password": "admin-pass"}).status_code == 201
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-pass"})
    return client, connection, {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_stack_membership_order_progress_and_reorder_api(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        stack = client.post("/api/v1/habit-stacks", headers=headers, json={"name": "Morning"})
        assert stack.status_code == 201
        stack_id = stack.json()["id"]
        first = client.post("/api/v1/habits", headers=headers, json={"title": "Meditate"})
        second = client.post("/api/v1/habits", headers=headers, json={"title": "Read"})
        first_id, second_id = first.json()["id"], second.json()["id"]
        added = client.post(f"/api/v1/habit-stacks/{stack_id}/habits/{first_id}", headers=headers)
        assert added.status_code == 200
        assert len(added.json()["habits"]) == 1
        client.post(f"/api/v1/habit-stacks/{stack_id}/habits/{second_id}", headers=headers)
        reordered = client.post(f"/api/v1/habit-stacks/{stack_id}/habits/reorder", headers=headers,
                                json={"ids": [second_id, first_id]})
        assert reordered.status_code == 204
        detail = client.get(f"/api/v1/habit-stacks/{stack_id}", headers=headers)
        assert [habit["id"] for habit in detail.json()["habits"]] == [second_id, first_id]
        assert detail.json()["scheduled_count"] == 2
        removed = client.delete(f"/api/v1/habit-stacks/{stack_id}/habits/{second_id}", headers=headers)
        assert removed.status_code == 200
        assert [habit["id"] for habit in removed.json()["habits"]] == [first_id]
    finally:
        connection.close()


def test_stack_ordering_archive_and_user_isolation(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        first = client.post("/api/v1/habit-stacks", headers=headers, json={"name": "First"})
        second = client.post("/api/v1/habit-stacks", headers=headers, json={"name": "Second"})
        first_id, second_id = first.json()["id"], second.json()["id"]
        assert client.post("/api/v1/habit-stacks/reorder", headers=headers, json={"ids": [second_id, first_id]}).status_code == 204
        listed = client.get("/api/v1/habit-stacks", headers=headers)
        assert [item["id"] for item in listed.json()] == [second_id, first_id]
        archived = client.patch(f"/api/v1/habit-stacks/{first_id}", headers=headers, json={"archived": True})
        assert archived.status_code == 200
        other = client.post("/api/v1/users", headers=headers, json={"username": "other", "display_name": "Other", "password": "other-pass"})
        login = client.post("/api/v1/auth/login", json={"username": "other", "password": "other-pass"})
        other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert other.status_code == 201
        assert client.get("/api/v1/habit-stacks", headers=other_headers).json() == []
        assert client.get(f"/api/v1/habit-stacks/{first_id}", headers=other_headers).status_code == 404
    finally:
        connection.close()
