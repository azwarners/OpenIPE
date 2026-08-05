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
    def delete(self, path, **kwargs): return self.request("DELETE", path, **kwargs)


def authenticated_client(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    client = ApiTestClient(create_app(connection=connection))
    assert client.post("/api/v1/setup/initial-admin", json={"username": "admin", "display_name": "Admin", "password": "admin-pass"}).status_code == 201
    login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-pass"})
    return client, connection, {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_habit_crud_schedule_and_checkin_api(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        created = client.post("/api/v1/habits", headers=headers, json={
            "title": "Exercise", "frequency_type": "times_per_week", "frequency_config": {"count": 3},
            "minimum_version": "Ten minutes",
        })
        assert created.status_code == 201
        habit_id = created.json()["id"]
        assert created.json()["minimum_version"] == "Ten minutes"
        checked = client.post(f"/api/v1/habits/{habit_id}/check-ins", headers=headers,
                              json={"date": "2026-08-05", "status": "completed", "note": "Done"})
        assert checked.status_code == 200
        assert checked.json()["status"] == "completed"
        updated = client.post(f"/api/v1/habits/{habit_id}/check-ins", headers=headers,
                              json={"date": "2026-08-05", "status": "skipped"})
        assert updated.status_code == 200
        assert updated.json()["id"] == checked.json()["id"]
        history = client.get(f"/api/v1/habits/{habit_id}/check-ins", headers=headers)
        assert history.status_code == 200
        assert history.json()[0]["status"] == "skipped"
        assert client.delete(f"/api/v1/habits/{habit_id}/check-ins/2026-08-05", headers=headers).status_code == 204
        archived = client.patch(f"/api/v1/habits/{habit_id}", headers=headers, json={"archived": True})
        assert archived.status_code == 200
        assert archived.json()["active"] is False
    finally:
        connection.close()


def test_inbox_habit_conversion_and_isolation(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        item = client.post("/api/v1/inbox", headers=headers, json={"text": "Meditate"})
        habit = client.post(f"/api/v1/inbox/{item.json()['id']}/create-habit", headers=headers,
                            json={"minimum_version": "Two minutes"})
        assert habit.status_code == 201
        assert habit.json()["source_inbox_item_id"] == item.json()["id"]
        assert client.get(f"/api/v1/inbox/{item.json()['id']}", headers=headers).json()["status"] == "unprocessed"
        other = client.post("/api/v1/users", headers=headers, json={"username": "other", "display_name": "Other", "password": "other-pass"})
        other_login = client.post("/api/v1/auth/login", json={"username": "other", "password": "other-pass"})
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
        assert other.status_code == 201
        assert client.get("/api/v1/habits", headers=other_headers).json() == []
    finally:
        connection.close()


def test_habit_requires_authentication_and_rejects_bad_schedule(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    client = ApiTestClient(create_app(connection=connection))
    try:
        assert client.get("/api/v1/habits").status_code == 401
        assert client.post("/api/v1/setup/initial-admin", json={"username": "admin", "display_name": "Admin", "password": "admin-pass"}).status_code == 201
        login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-pass"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = client.post("/api/v1/habits", headers=headers, json={"title": "Bad", "frequency_type": "selected_days", "frequency_config": {"days": [8]}})
        assert response.status_code == 400
    finally:
        connection.close()
