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

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def patch(self, path, **kwargs):
        return self.request("PATCH", path, **kwargs)


def authenticated_client(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    client = ApiTestClient(create_app(connection=connection))
    setup = client.post(
        "/api/v1/setup/initial-admin",
        json={"username": "admin", "display_name": "Administrator", "password": "admin-pass"},
    )
    assert setup.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin-pass"},
    )
    assert login.status_code == 200
    return client, connection, {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_goal_crud_lifecycle_and_status_filter(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        created = client.post(
            "/api/v1/goals",
            headers=headers,
            json={"title": "  Publish OpenIPE  ", "description": "First release", "target_date": "2026-12-31"},
        )
        assert created.status_code == 201
        goal = created.json()
        assert goal["title"] == "Publish OpenIPE"
        assert goal["status"] == "active"
        goal_id = goal["id"]

        paused = client.patch(
            f"/api/v1/goals/{goal_id}", headers=headers, json={"status": "paused"}
        )
        assert paused.status_code == 200
        assert paused.json()["status"] == "paused"
        achieved = client.patch(
            f"/api/v1/goals/{goal_id}", headers=headers, json={"status": "active"}
        )
        assert achieved.status_code == 200
        achieved = client.patch(
            f"/api/v1/goals/{goal_id}", headers=headers, json={"status": "achieved"}
        )
        assert achieved.status_code == 200
        assert achieved.json()["achieved_at"] is not None
        active = client.get("/api/v1/goals?status=active", headers=headers)
        assert active.status_code == 200
        assert active.json() == []
    finally:
        connection.close()


def test_goal_source_and_user_isolation(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        inbox = client.post("/api/v1/inbox", headers=headers, json={"text": "Goal source"})
        goal = client.post(
            "/api/v1/goals",
            headers=headers,
            json={"title": "Goal", "source_inbox_item_id": inbox.json()["id"]},
        )
        assert goal.status_code == 201
        goal_id = goal.json()["id"]
        assert goal.json()["source_inbox_item_id"] == inbox.json()["id"]

        other = client.post(
            "/api/v1/users",
            headers=headers,
            json={"username": "other", "display_name": "Other", "password": "other-pass"},
        )
        other_login = client.post(
            "/api/v1/auth/login", json={"username": "other", "password": "other-pass"}
        )
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
        assert other.status_code == 201
        assert client.get("/api/v1/goals", headers=other_headers).json() == []
        assert client.get(f"/api/v1/goals/{goal_id}", headers=other_headers).status_code == 404
        assert client.post(
            "/api/v1/goals",
            headers=other_headers,
            json={"title": "Invalid source", "source_inbox_item_id": inbox.json()["id"]},
        ).status_code == 400
    finally:
        connection.close()


def test_goals_require_authentication_and_validate_title(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    client = ApiTestClient(create_app(connection=connection))
    try:
        assert client.get("/api/v1/goals").status_code == 401
        setup = client.post(
            "/api/v1/setup/initial-admin",
            json={"username": "admin", "display_name": "Admin", "password": "admin-pass"},
        )
        login = client.post(
            "/api/v1/auth/login", json={"username": "admin", "password": "admin-pass"}
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert setup.status_code == 201
        assert client.post("/api/v1/goals", headers=headers, json={"title": "   "}).status_code == 400
    finally:
        connection.close()
