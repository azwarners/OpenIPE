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

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)


def make_client(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    return ApiTestClient(create_app(connection=connection)), connection


def authenticated_client(tmp_path):
    client, connection = make_client(tmp_path)
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


def test_capture_edit_process_archive_and_filter_via_api(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        created = client.post("/api/v1/inbox", headers=headers, json={"text": "Capture this thought"})
        assert created.status_code == 201
        item = created.json()
        assert item["status"] == "unprocessed"
        item_id = item["id"]

        edited = client.patch(
            f"/api/v1/inbox/{item_id}",
            headers=headers,
            json={"text": "Edited thought", "status": "processed"},
        )
        assert edited.status_code == 200
        assert edited.json()["text"] == "Edited thought"
        assert edited.json()["processed_at"] is not None

        processed = client.get("/api/v1/inbox?status=processed", headers=headers)
        assert processed.status_code == 200
        assert [entry["id"] for entry in processed.json()] == [item_id]

        deleted = client.delete(f"/api/v1/inbox/{item_id}", headers=headers)
        assert deleted.status_code == 204
        detail = client.get(f"/api/v1/inbox/{item_id}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["status"] == "archived"
    finally:
        connection.close()


def test_inbox_requires_authentication_and_hides_other_users_items(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        created = client.post("/api/v1/inbox", headers=headers, json={"text": "Private idea"})
        item_id = created.json()["id"]
        assert client.get("/api/v1/inbox").status_code == 401

        other = client.post(
            "/api/v1/users",
            headers=headers,
            json={"username": "other", "display_name": "Other", "password": "other-pass"},
        )
        other_login = client.post(
            "/api/v1/auth/login",
            json={"username": "other", "password": "other-pass"},
        )
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
        assert other.status_code == 201
        assert client.get("/api/v1/inbox", headers=other_headers).json() == []
        assert client.get(f"/api/v1/inbox/{item_id}", headers=other_headers).status_code == 404
        assert client.patch(
            f"/api/v1/inbox/{item_id}", headers=other_headers, json={"text": "tamper"}
        ).status_code == 404
    finally:
        connection.close()


def test_invalid_inbox_text_is_rejected(tmp_path):
    client, connection, headers = authenticated_client(tmp_path)
    try:
        response = client.post("/api/v1/inbox", headers=headers, json={"text": "   "})
        assert response.status_code == 400
        assert "empty" in response.json()["detail"]
    finally:
        connection.close()
