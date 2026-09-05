"""Route-by-route real HTTP contract matrix."""

import pytest

from tests.test_api_auth import create_admin, login, make_client


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/api/v1/auth/me", id="auth-me"),
        pytest.param("/api/v1/users", id="users"),
        pytest.param("/api/v1/inbox", id="inbox"),
        pytest.param("/api/v1/inbox?status=unprocessed", id="inbox-filter"),
        pytest.param("/api/v1/goals", id="goals"),
        pytest.param("/api/v1/goals?status=active", id="goals-filter"),
        pytest.param("/api/v1/projects", id="projects"),
        pytest.param("/api/v1/tasks", id="tasks"),
        pytest.param("/api/v1/tasks?status=open", id="tasks-filter"),
        pytest.param("/api/v1/habits", id="habits"),
        pytest.param("/api/v1/habits?active=true", id="habits-active"),
        pytest.param("/api/v1/habits?active=false", id="habits-inactive"),
        pytest.param("/api/v1/habit-stacks", id="stacks"),
        pytest.param("/api/v1/habit-stacks?active=true", id="stacks-active"),
        pytest.param("/api/v1/habit-stacks?active=false", id="stacks-inactive"),
        pytest.param("/api/v1/today", id="today-default"),
        pytest.param("/api/v1/today?include_completed=false", id="today-open"),
        pytest.param("/api/v1/today?include_completed=true", id="today-completed"),
    ],
)
def test_every_collection_route_returns_a_schema_valid_success(path, tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        headers = {"Authorization": f"Bearer {login(client)['access_token']}"}
        response = client.get(path, headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert isinstance(response.json(), (list, dict))
    finally:
        connection.close()


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/api/v1/auth/me", id="me"),
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
def test_every_protected_route_maps_missing_auth_to_401(path, tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        response = client.get(path)
        assert response.status_code == 401
        assert "detail" in response.json()
    finally:
        connection.close()


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/api/v1/today?date=bad", id="today-date"),
        pytest.param("/api/v1/today?include_completed=bad", id="today-bool"),
        pytest.param("/api/v1/goals?status=bad", id="goal-status"),
        pytest.param("/api/v1/inbox?status=bad", id="inbox-status"),
        pytest.param("/api/v1/tasks?status=bad", id="task-status"),
        pytest.param("/api/v1/habits?active=bad", id="habit-active"),
        pytest.param("/api/v1/habit-stacks?active=bad", id="stack-active"),
        pytest.param("/api/v1/habits/1/check-ins?limit=0", id="limit-zero"),
        pytest.param("/api/v1/habits/1/check-ins?limit=101", id="limit-large"),
        pytest.param("/api/v1/inbox/no", id="inbox-id"),
        pytest.param("/api/v1/goals/no", id="goal-id"),
        pytest.param("/api/v1/tasks/no", id="task-id"),
    ],
)
def test_route_query_and_path_validation_matrix_returns_422(path, tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        headers = {"Authorization": f"Bearer {login(client)['access_token']}"}
        response = client.get(path, headers=headers)
        assert response.status_code == 422
        assert response.json()["detail"]
    finally:
        connection.close()


@pytest.mark.parametrize(
    "path,payload",
    [
        pytest.param("/api/v1/inbox", {"text": "http idea"}, id="inbox"),
        pytest.param("/api/v1/projects", {"title": "http project"}, id="project"),
        pytest.param("/api/v1/tasks", {"title": "http task", "priority": "high", "is_today": True}, id="task"),
        pytest.param("/api/v1/goals", {"title": "http goal", "target_date": "2026-08-01"}, id="goal"),
        pytest.param("/api/v1/habits", {"title": "http habit", "frequency_type": "daily"}, id="habit"),
        pytest.param("/api/v1/habit-stacks", {"name": "http stack"}, id="stack"),
        pytest.param("/api/v1/setup/initial-admin", {"username": "new", "display_name": "New", "password": "new-pass"}, id="setup-second-is-invalid"),
    ],
)
def test_route_body_matrix_preserves_success_or_domain_error_contract(path, payload, tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        headers = {"Authorization": f"Bearer {login(client)['access_token']}"}
        response = client.post(path, headers=headers, json=payload)
        if path.endswith("initial-admin"):
            assert response.status_code == 409
        else:
            assert response.status_code == 201
            assert isinstance(response.json()["id"], int)
    finally:
        connection.close()
