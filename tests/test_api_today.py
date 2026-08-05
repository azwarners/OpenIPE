import asyncio
from datetime import date

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


def test_today_api_aggregates_selected_date(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    client = ApiTestClient(create_app(connection=connection))
    try:
        assert client.post("/api/v1/setup/initial-admin", json={"username": "admin", "display_name": "Admin", "password": "admin-pass"}).status_code == 201
        login = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin-pass"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        selected = date(2026, 8, 5)
        task = client.post("/api/v1/tasks", headers=headers, json={"title": "Today task", "is_today": True})
        habit = client.post("/api/v1/habits", headers=headers, json={"title": "Daily habit"})
        checkin = client.post(f"/api/v1/habits/{habit.json()['id']}/check-ins", headers=headers,
                              json={"date": selected.isoformat(), "status": "completed"})
        assert task.status_code == 201 and checkin.status_code == 200
        response = client.get(f"/api/v1/today?date={selected.isoformat()}", headers=headers)
        assert response.status_code == 200
        payload = response.json()
        assert payload["date"] == selected.isoformat()
        assert payload["tasks"][0]["id"] == task.json()["id"]
        assert payload["unstacked_habits"][0]["today_status"] == "completed"
        assert payload["completed"]["tasks"] == []
        assert client.get(f"/api/v1/today?date={selected.isoformat()}&include_completed=true", headers=headers).status_code == 200
    finally:
        connection.close()


def test_today_requires_authentication(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    client = ApiTestClient(create_app(connection=connection))
    try:
        assert client.get("/api/v1/today").status_code == 401
    finally:
        connection.close()
