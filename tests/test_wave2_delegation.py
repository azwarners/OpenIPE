"""Focused injected-façade delegation checks, separate from real workflows."""

import asyncio

import httpx
import pytest

from openipe.api.REST.app import create_app
from tests.test_rest_delegation import SpyAPI


@pytest.mark.parametrize(
    "family",
    [
        pytest.param("auth", id="auth-login"),
        pytest.param("users", id="users-create"),
        pytest.param("inbox", id="inbox-create"),
        pytest.param("goals", id="goal-project-association"),
        pytest.param("projects", id="project-create"),
        pytest.param("tasks", id="task-create"),
        pytest.param("habits", id="habit-checkin"),
        pytest.param("stacks", id="stack-reorder"),
        pytest.param("today", id="today-query"),
    ],
)
def test_each_rest_family_delegates_exactly_once_with_opaque_context(family):
    spy = SpyAPI()
    app = create_app(spy)

    async def exercise():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            if family == "auth":
                response = await client.post("/api/v1/auth/login", json={"username": "a", "password": "p"})
                expected = "login"
            else:
                headers = {"Authorization": "Bearer token"}
                if family == "users":
                    response = await client.post("/api/v1/users", headers=headers, json={"username": "u", "display_name": "U", "password": "p"})
                    expected = "create_user"
                elif family == "inbox":
                    response = await client.post("/api/v1/inbox", headers=headers, json={"text": "idea"})
                    expected = "create_inbox"
                elif family == "goals":
                    response = await client.post("/api/v1/goals/3/projects/4", headers=headers)
                    expected = "associate"
                elif family == "projects":
                    response = await client.post("/api/v1/projects", headers=headers, json={"title": "Project"})
                    expected = "create_project"
                elif family == "tasks":
                    response = await client.post("/api/v1/tasks", headers=headers, json={"title": "Task", "is_today": True})
                    expected = "create_task"
                elif family == "habits":
                    response = await client.post("/api/v1/habits/2/check-ins", headers=headers, json={"date": "2026-06-01", "status": "skipped", "note": "later"})
                    expected = "check_in"
                elif family == "stacks":
                    response = await client.post("/api/v1/habit-stacks/reorder", headers=headers, json={"ids": [7, 8]})
                    expected = "reorder_stacks"
                else:
                    response = await client.get("/api/v1/today?date=2026-06-01&include_completed=true", headers=headers)
                    expected = "today"
            assert response.status_code in {200, 201, 204}
        return expected

    expected = asyncio.run(exercise())
    names = [call[0] for call in spy.calls]
    assert names.count(expected) == 1
    assert names.count("authenticate") == (0 if family == "auth" else 1)
    if family == "users":
        assert names.count("authorize_admin") == 1
    if family != "auth":
        operation = next(call for call in spy.calls if call[0] == expected)
        if family in {"users", "inbox"}:
            assert operation[1] is spy.context
        elif family == "goals":
            assert operation[1:] == (spy.context, 3, 4, "project")
        elif family == "habits":
            assert operation[1][0] is spy.context
            assert operation[1][2].date.isoformat() == "2026-06-01"
        elif family == "stacks":
            assert operation[1][0] is spy.context
            assert operation[1][1].ids == (7, 8)
        elif family == "today":
            assert operation[1][0] is spy.context
            assert operation[1][1].include_completed is True
