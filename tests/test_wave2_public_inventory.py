"""Explicit public-operation and route-boundary coverage checks."""

import pytest

from tests.internal_support import admin, make_internal
from tests.test_api_auth import create_admin, login, make_client


@pytest.mark.parametrize(
    "operation",
    [
        pytest.param("auth.current_user", id="auth-current-user"),
        pytest.param("users.get", id="users-get"),
        pytest.param("inbox.get", id="inbox-get"),
        pytest.param("goals.get", id="goals-get"),
        pytest.param("projects.get", id="projects-get"),
        pytest.param("tasks.get", id="tasks-get"),
        pytest.param("habits.get", id="habits-get"),
        pytest.param("habit_stacks.get", id="habit-stacks-get"),
        pytest.param("today.get", id="today-get"),
    ],
)
def test_public_namespace_getters_return_internal_contracts(operation, tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        user = api.users.create(context, "visible", "Visible", "visible-pass")
        inbox = api.inbox.create(context, "idea")
        goal = api.goals.create(context, "goal")
        project = api.projects.create(context, "project")
        task = api.tasks.create(context, "task")
        habit = api.habits.create(context, "habit")
        stack = api.habit_stacks.create(context, "stack")
        values = {
            "auth.current_user": api.auth.current_user(context),
            "users.get": api.users.get(context, user.id),
            "inbox.get": api.inbox.get(context, inbox.id),
            "goals.get": api.goals.get(context, goal.id),
            "projects.get": api.projects.get(context, project.id),
            "tasks.get": api.tasks.get(context, task.id),
            "habits.get": api.habits.get(context, habit.id),
            "habit_stacks.get": api.habit_stacks.get(context, stack.id),
            "today.get": api.today.get(context),
        }
        result = values[operation]
        assert result.__class__.__module__ == "openipe.api.internal.contracts"
        assert "sqlite3" not in repr(result)
        assert "password_hash" not in repr(result)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/api/v1/inbox/not-an-id", id="inbox"),
        pytest.param("/api/v1/goals/not-an-id", id="goals"),
        pytest.param("/api/v1/projects/not-an-id", id="projects"),
        pytest.param("/api/v1/tasks/not-an-id", id="tasks"),
        pytest.param("/api/v1/habits/not-an-id", id="habits"),
        pytest.param("/api/v1/habit-stacks/not-an-id", id="stacks"),
        pytest.param("/api/v1/users/not-an-id", id="users"),
        pytest.param("/api/v1/habits/1/check-ins/not-a-date", id="check-in-date"),
    ],
)
def test_resource_id_route_matrix_returns_http_validation(path, tmp_path):
    client, connection = make_client(tmp_path)
    try:
        create_admin(client)
        headers = {"Authorization": f"Bearer {login(client)['access_token']}"}
        method = "DELETE" if "check-ins/not-a-date" in path else "GET"
        response = client.request(method, path, headers=headers)
        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        connection.close()
