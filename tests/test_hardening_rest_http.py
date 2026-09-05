"""HTTP contract tests for malformed input, auth, and isolation boundaries."""

from tests.test_api_auth import create_admin, login, make_client


def test_rest_rejects_missing_and_wrongly_typed_required_fields(tmp_path):
    client, connection = make_client(tmp_path)
    try:
        assert client.post("/api/v1/setup/initial-admin", json={}).status_code == 422
        create_admin(client)
        token = login(client)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.post("/api/v1/inbox", headers=headers, json={}).status_code == 422
        assert client.post("/api/v1/inbox", headers=headers, json={"text": 42}).status_code == 422
        assert client.post("/api/v1/tasks", headers=headers, json={"title": []}).status_code == 422
    finally:
        connection.close()


def test_rest_rejects_invalid_query_path_and_enum_values(tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        token = login(client)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/v1/today?date=not-a-date", headers=headers).status_code == 422
        assert client.get("/api/v1/habits/1/check-ins?limit=0", headers=headers).status_code == 422
        assert client.get("/api/v1/tasks?status=not-a-status", headers=headers).status_code == 422
        assert client.get("/api/v1/inbox/not-an-id", headers=headers).status_code == 422
    finally:
        connection.close()


def test_rest_preserves_authentication_and_not_found_status_mappings(tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        assert client.get("/api/v1/inbox").status_code == 401
        assert client.get("/api/v1/inbox", headers={"Authorization": "Bearer"}).status_code == 401
        token = login(client)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/v1/inbox/99999", headers=headers).status_code == 404
        assert client.get("/api/v1/inbox/99999", headers=headers).headers["content-type"].startswith("application/json")
    finally:
        connection.close()


def test_rest_cross_user_records_are_not_visible(tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        admin_token = login(client)["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        created = client.post(
            "/api/v1/users", headers=admin_headers,
            json={"username": "other", "display_name": "Other", "password": "other-pass"},
        )
        assert created.status_code == 201
        private = client.post("/api/v1/inbox", headers=admin_headers, json={"text": "private"})
        other_token = login(client, "other", "other-pass")["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}
        assert client.get("/api/v1/inbox", headers=other_headers).json() == []
        assert client.get(f"/api/v1/inbox/{private.json()['id']}", headers=other_headers).status_code == 404
    finally:
        connection.close()


def test_rest_repeated_lifecycle_requests_preserve_domain_errors(tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        headers = {"Authorization": f"Bearer {login(client)['access_token']}"}
        task = client.post("/api/v1/tasks", headers=headers, json={"title": "once"}).json()
        assert client.post(f"/api/v1/tasks/{task['id']}/complete", headers=headers).status_code == 200
        repeated = client.post(f"/api/v1/tasks/{task['id']}/complete", headers=headers)
        assert repeated.status_code in {400, 409}
        assert "detail" in repeated.json()
    finally:
        connection.close()
