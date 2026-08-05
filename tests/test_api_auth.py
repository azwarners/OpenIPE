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


def make_client(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    app = create_app(connection=connection)
    return ApiTestClient(app), connection


def create_admin(client):
    response = client.post(
        "/api/v1/setup/initial-admin",
        json={
            "username": "admin",
            "display_name": "Administrator",
            "password": "admin-pass",
        },
    )
    assert response.status_code == 201
    return response.json()


def login(client, username="admin", password="admin-pass"):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def test_initial_setup_login_me_and_logout(tmp_path):
    client, connection = make_client(tmp_path)
    try:
        admin = create_admin(client)
        assert admin["username"] == "admin"
        assert "password_hash" not in admin

        duplicate = client.post(
            "/api/v1/setup/initial-admin",
            json={"username": "other", "display_name": "Other", "password": "other-pass"},
        )
        assert duplicate.status_code == 409

        result = login(client)
        token = result["access_token"]
        assert result["token_type"] == "bearer"
        assert result["user"]["id"] == admin["id"]

        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["username"] == "admin"

        logout = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert logout.status_code == 204
        assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    finally:
        connection.close()


def test_authentication_errors_are_safe_and_consistent(tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        assert client.get("/api/v1/auth/me").status_code == 401
        bad_login = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong-pass"},
        )
        assert bad_login.status_code == 401
        assert "wrong-pass" not in bad_login.text
        assert client.get(
            "/api/v1/auth/me", headers={"Authorization": "Basic abc"}
        ).status_code == 401
    finally:
        connection.close()


def test_admin_user_management_and_deactivation(tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        token = login(client)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        created = client.post(
            "/api/v1/users",
            headers=headers,
            json={"username": "user", "display_name": "User", "password": "user-pass"},
        )
        assert created.status_code == 201
        user_id = created.json()["id"]
        assert len(client.get("/api/v1/users", headers=headers).json()) == 2

        updated = client.patch(
            f"/api/v1/users/{user_id}",
            headers=headers,
            json={"display_name": "Renamed User", "is_active": False},
        )
        assert updated.status_code == 200
        assert updated.json()["display_name"] == "Renamed User"
        assert updated.json()["is_active"] is False
        assert client.post(
            "/api/v1/auth/login",
            json={"username": "user", "password": "user-pass"},
        ).status_code == 403
    finally:
        connection.close()


def test_non_admin_cannot_manage_users(tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        admin_token = login(client)["access_token"]
        created = client.post(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"username": "user", "display_name": "User", "password": "user-pass"},
        )
        user_token = login(client, "user", "user-pass")["access_token"]
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403
        assert created.status_code == 201
    finally:
        connection.close()


def test_change_password_invalidates_old_token(tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        old_token = login(client)["access_token"]
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {old_token}"},
            json={"current_password": "admin-pass", "new_password": "new-admin-pass"},
        )
        assert response.status_code == 204
        assert client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {old_token}"},
        ).status_code == 401
        assert login(client, password="new-admin-pass")["user"]["username"] == "admin"
    finally:
        connection.close()
