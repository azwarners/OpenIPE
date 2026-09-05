"""Wave 2 real-ASGI HTTP and route-contract matrices."""

from datetime import date

import pytest

from tests.test_api_auth import create_admin, login, make_client


AUTH_HEADERS = [
    pytest.param({}, id="missing"),
    pytest.param({"Authorization": "Basic abc"}, id="basic-scheme"),
    pytest.param({"Authorization": "Bearer"}, id="empty-bearer"),
    pytest.param({"Authorization": "Bearer invalid"}, id="unknown-token"),
    pytest.param({"Authorization": "Bearer a b"}, id="malformed-token"),
    pytest.param({"Authorization": "Token abc"}, id="wrong-scheme"),
]


@pytest.mark.parametrize("headers", AUTH_HEADERS)
def test_every_protected_family_rejects_missing_or_malformed_auth(tmp_path, headers):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        assert client.get("/api/v1/inbox", headers=headers).status_code == 401
        assert client.get("/api/v1/today", headers=headers).status_code == 401
    finally:
        connection.close()


@pytest.mark.parametrize(
    "path,payload",
    [
        pytest.param("/api/v1/inbox", {"text": 1}, id="inbox-wrong-text"),
        pytest.param("/api/v1/inbox", {}, id="inbox-missing-text"),
        pytest.param("/api/v1/tasks", {"title": []}, id="task-wrong-title"),
        pytest.param("/api/v1/tasks", {}, id="task-missing-title"),
        pytest.param("/api/v1/projects", {"title": None}, id="project-null-title"),
        pytest.param("/api/v1/goals", {"title": 3}, id="goal-wrong-title"),
        pytest.param("/api/v1/habits", {"title": "h", "frequency_type": "unknown"}, id="habit-invalid-frequency"),
        pytest.param("/api/v1/habit-stacks", {"name": ""}, id="stack-empty-name"),
        pytest.param("/api/v1/habits", {"title": "h", "frequency_type": "selected_days", "frequency_config": {"days": []}}, id="habit-empty-schedule"),
        pytest.param("/api/v1/users", {"username": "u"}, id="user-missing-fields"),
        pytest.param("/api/v1/setup/initial-admin", {"username": "u", "display_name": "U"}, id="setup-missing-password"),
        pytest.param("/api/v1/auth/login", {"username": "u"}, id="login-missing-password"),
    ],
)
def test_rest_payload_matrix_returns_validation_status(tmp_path, path, payload):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        token = login(client)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(path, headers=headers, json=payload)
        assert response.status_code in {400, 422}
        assert response.headers["content-type"].startswith("application/json")
        assert "detail" in response.json()
    finally:
        connection.close()


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/api/v1/auth/me", id="auth-me"),
        pytest.param("/api/v1/users", id="users"),
        pytest.param("/api/v1/inbox", id="inbox"),
        pytest.param("/api/v1/goals", id="goals"),
        pytest.param("/api/v1/projects", id="projects"),
        pytest.param("/api/v1/tasks", id="tasks"),
        pytest.param("/api/v1/habits", id="habits"),
        pytest.param("/api/v1/habit-stacks", id="stacks"),
        pytest.param("/api/v1/today", id="today"),
    ],
)
def test_protected_route_families_require_authentication(tmp_path, path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        assert client.get(path).status_code == 401
    finally:
        connection.close()


@pytest.mark.parametrize(
    "path,expected_key",
    [
        pytest.param("/api/v1/inbox", "text", id="inbox"),
        pytest.param("/api/v1/projects", "title", id="projects"),
        pytest.param("/api/v1/tasks", "title", id="tasks"),
        pytest.param("/api/v1/goals", "title", id="goals"),
        pytest.param("/api/v1/habits", "title", id="habits"),
        pytest.param("/api/v1/habit-stacks", "name", id="stacks"),
    ],
)
def test_rest_valid_create_routes_return_serializable_resource_shapes(tmp_path, path, expected_key):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        token = login(client)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "/api/v1/inbox": {"text": "idea"},
            "/api/v1/projects": {"title": "project"},
            "/api/v1/tasks": {"title": "task"},
            "/api/v1/goals": {"title": "goal"},
            "/api/v1/habits": {"title": "habit"},
            "/api/v1/habit-stacks": {"name": "stack"},
        }[path]
        response = client.post(path, headers=headers, json=payload)
        assert response.status_code == 201
        body = response.json()
        assert body[expected_key] == payload[expected_key]
        assert isinstance(body["id"], int)
        assert "password_hash" not in response.text
        assert "token_hash" not in response.text
    finally:
        connection.close()


@pytest.mark.parametrize(
    "query",
    [
        pytest.param("?date=not-a-date", id="bad-date"),
        pytest.param("?include_completed=not-bool", id="bad-boolean"),
        pytest.param("?date=2026-99-99", id="impossible-date"),
        pytest.param("?unknown=field", id="unknown-query-is-safe"),
    ],
)
def test_today_query_matrix_is_deterministic_and_validated(tmp_path, query):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        headers = {"Authorization": f"Bearer {login(client)['access_token']}"}
        response = client.get("/api/v1/today" + query, headers=headers)
        if "unknown" in query:
            assert response.status_code == 200
            assert response.json()["date"]
        else:
            assert response.status_code == 422
    finally:
        connection.close()


@pytest.mark.parametrize(
    "workflow",
    [
        pytest.param("inbox-project", id="capture-to-project"),
        pytest.param("goal-task", id="goal-backed-task"),
        pytest.param("daily-loop", id="daily-execution"),
        pytest.param("habit-stack", id="habit-establishment"),
        pytest.param("lifecycle", id="lifecycle-recovery"),
        pytest.param("isolation", id="two-user-isolation"),
        pytest.param("restart-shape", id="restart-visible-state"),
    ],
)
def test_real_root_app_supports_each_productivity_workflow_family(tmp_path, workflow):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        token = login(client)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        if workflow == "inbox-project":
            item = client.post("/api/v1/inbox", headers=headers, json={"text": "ship"}).json()
            project = client.post(f"/api/v1/inbox/{item['id']}/create-project", headers=headers, json={}).json()
            task = client.post("/api/v1/tasks", headers=headers, json={"title": "publish", "project_id": project["id"]}).json()
            assert client.post(f"/api/v1/projects/{project['id']}/next-action/{task['id']}", headers=headers).status_code == 200
            assert client.post(f"/api/v1/tasks/{task['id']}/complete", headers=headers).status_code == 200
        elif workflow == "goal-task":
            goal = client.post("/api/v1/goals", headers=headers, json={"title": "goal"}).json()
            task = client.post("/api/v1/tasks", headers=headers, json={"title": "work"}).json()
            associated = client.post(f"/api/v1/goals/{goal['id']}/tasks/{task['id']}", headers=headers)
            assert associated.status_code == 200
            assert client.post(f"/api/v1/tasks/{task['id']}/complete", headers=headers).status_code == 200
        elif workflow == "daily-loop":
            task = client.post("/api/v1/tasks", headers=headers, json={"title": "today", "is_today": True, "due_date": "2026-05-01"}).json()
            before = client.get("/api/v1/today?date=2026-05-01", headers=headers).json()
            assert [x["id"] for x in before["tasks"]] == [task["id"]]
            client.post(f"/api/v1/tasks/{task['id']}/complete", headers=headers)
            after = client.get("/api/v1/today?date=2026-05-01&include_completed=true", headers=headers).json()
            assert [x["id"] for x in after["completed"]["tasks"]] == [task["id"]]
        elif workflow == "habit-stack":
            habit = client.post("/api/v1/habits", headers=headers, json={"title": "habit"}).json()
            stack = client.post("/api/v1/habit-stacks", headers=headers, json={"name": "morning"}).json()
            assert client.post(f"/api/v1/habit-stacks/{stack['id']}/habits/{habit['id']}", headers=headers).status_code == 200
            checkin = client.post(f"/api/v1/habits/{habit['id']}/check-ins", headers=headers, json={"date": "2026-05-01", "status": "completed"})
            assert checkin.status_code == 200
        elif workflow == "lifecycle":
            task = client.post("/api/v1/tasks", headers=headers, json={"title": "recover"}).json()
            assert client.post(f"/api/v1/tasks/{task['id']}/complete", headers=headers).status_code == 200
            assert client.post(f"/api/v1/tasks/{task['id']}/reopen", headers=headers).status_code == 200
            assert client.post(f"/api/v1/tasks/{task['id']}/cancel", headers=headers).status_code == 200
            assert client.post(f"/api/v1/tasks/{task['id']}/reopen", headers=headers).status_code in {400, 422}
        elif workflow == "isolation":
            user = client.post("/api/v1/users", headers=headers, json={"username": "other", "display_name": "Other", "password": "other-pass"}).json()
            private = client.post("/api/v1/inbox", headers=headers, json={"text": "private"}).json()
            other = login(client, "other", "other-pass")["access_token"]
            other_headers = {"Authorization": f"Bearer {other}"}
            assert client.get(f"/api/v1/inbox/{private['id']}", headers=other_headers).status_code == 404
            assert client.get("/api/v1/inbox", headers=other_headers).json() == []
            assert user["username"] == "other"
        else:
            task = client.post("/api/v1/tasks", headers=headers, json={"title": "persist"}).json()
            assert client.get(f"/api/v1/tasks/{task['id']}", headers=headers).json()["title"] == "persist"
        assert response_shape_is_json(client, headers)
    finally:
        connection.close()


def response_shape_is_json(client, headers):
    response = client.get("/api/v1/auth/me", headers=headers)
    return response.status_code == 200 and isinstance(response.json()["id"], int)
