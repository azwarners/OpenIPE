"""True root-factory restart tests using owned file-backed SQLite state."""

import asyncio

import httpx
import pytest

from openipe.api.app import create_app
from openipe.core.config import Settings


class RootSession:
    """Synchronous test wrapper keeping one real lifespan around HTTP calls."""

    def __init__(self, app):
        self.app = app
        self.loop = asyncio.new_event_loop()
        self.context = app.router.lifespan_context(app)
        self.loop.run_until_complete(self.context.__aenter__())

    def request(self, method, path, **kwargs):
        async def send():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test") as client:
                return await client.request(method, path, **kwargs)
        return self.loop.run_until_complete(send())

    def close(self):
        self.loop.run_until_complete(self.context.__aexit__(None, None, None))
        self.loop.close()


_SESSIONS = {}


def run_request(app, method, path, **kwargs):
    session = _SESSIONS.get(id(app))
    if session is None:
        session = RootSession(app)
        _SESSIONS[id(app)] = session
    return session.request(method, path, **kwargs)


def close_owned_app(app):
    _SESSIONS.pop(id(app)).close()


def setup_app(path):
    return create_app(settings=Settings(database_path=path))


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param("project-goal", id="project-goal-associations"),
        pytest.param("habit-stack", id="habit-stack-history"),
        pytest.param("terminal-states", id="terminal-state-timestamps"),
        pytest.param("two-users", id="multiple-user-isolation"),
        pytest.param("rollback", id="failed-mutation-rollback"),
        pytest.param("migration-repeat", id="migration-idempotency"),
        pytest.param("today", id="today-persistence"),
    ],
)
def test_root_app_restart_preserves_committed_productivity_state(tmp_path, scenario):
    path = tmp_path / "restart.sqlite3"
    app = setup_app(path)
    setup = run_request(app, "POST", "/api/v1/setup/initial-admin", json={"username": "admin", "display_name": "Admin", "password": "admin-pass"})
    assert setup.status_code == 201
    login = run_request(app, "POST", "/api/v1/auth/login", json={"username": "admin", "password": "admin-pass"}).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    if scenario == "project-goal":
        item = run_request(app, "POST", "/api/v1/inbox", headers=headers, json={"text": "launch"}).json()
        project = run_request(app, "POST", f"/api/v1/inbox/{item['id']}/create-project", headers=headers, json={}).json()
        task = run_request(app, "POST", "/api/v1/tasks", headers=headers, json={"title": "ship", "project_id": project["id"]}).json()
        goal = run_request(app, "POST", "/api/v1/goals", headers=headers, json={"title": "release"}).json()
        assert run_request(app, "POST", f"/api/v1/goals/{goal['id']}/projects/{project['id']}", headers=headers).status_code == 200
        assert run_request(app, "POST", f"/api/v1/projects/{project['id']}/next-action/{task['id']}", headers=headers).status_code == 200
    elif scenario == "habit-stack":
        habit = run_request(app, "POST", "/api/v1/habits", headers=headers, json={"title": "daily"}).json()
        stack = run_request(app, "POST", "/api/v1/habit-stacks", headers=headers, json={"name": "morning"}).json()
        assert run_request(app, "POST", f"/api/v1/habit-stacks/{stack['id']}/habits/{habit['id']}", headers=headers).status_code == 200
        assert run_request(app, "POST", f"/api/v1/habits/{habit['id']}/check-ins", headers=headers, json={"date": "2026-07-01", "status": "completed"}).status_code == 200
    elif scenario == "terminal-states":
        task = run_request(app, "POST", "/api/v1/tasks", headers=headers, json={"title": "done"}).json()
        assert run_request(app, "POST", f"/api/v1/tasks/{task['id']}/complete", headers=headers).status_code == 200
        archived = run_request(app, "PATCH", f"/api/v1/tasks/{task['id']}", headers=headers, json={"status": "archived"})
        assert archived.status_code == 200
    elif scenario == "two-users":
        user = run_request(app, "POST", "/api/v1/users", headers=headers, json={"username": "other", "display_name": "Other", "password": "other-pass"}).json()
        private = run_request(app, "POST", "/api/v1/inbox", headers=headers, json={"text": "private"}).json()
    elif scenario == "rollback":
        failed = run_request(app, "POST", "/api/v1/tasks", headers=headers, json={"title": "bad", "project_id": 999999})
        assert failed.status_code == 400
    elif scenario == "migration-repeat":
        assert run_request(app, "GET", "/api/v1/auth/me", headers=headers).status_code == 200
    else:
        task = run_request(app, "POST", "/api/v1/tasks", headers=headers, json={"title": "today", "is_today": True}).json()
        assert run_request(app, "GET", "/api/v1/today?date=2026-07-01", headers=headers).status_code == 200

    first_connection = app.state.internal_api.connection
    close_owned_app(app)
    with pytest.raises(Exception):
        first_connection.execute("SELECT 1")
    # The owned connection is now closed; construct a fresh root app to prove
    # persisted state independently.
    reopened = setup_app(path)
    relogin = run_request(reopened, "POST", "/api/v1/auth/login", json={"username": "admin", "password": "admin-pass"})
    assert relogin.status_code == 200
    reopened_headers = {"Authorization": f"Bearer {relogin.json()['access_token']}"}
    assert run_request(reopened, "GET", "/api/v1/auth/me", headers=reopened_headers).status_code == 200
    if scenario == "project-goal":
        assert run_request(reopened, "GET", "/api/v1/projects", headers=reopened_headers).json()[0]["task_ids"]
        assert run_request(reopened, "GET", "/api/v1/goals", headers=reopened_headers).json()[0]["project_ids"]
    elif scenario == "habit-stack":
        assert run_request(reopened, "GET", "/api/v1/habit-stacks", headers=reopened_headers).json()[0]["habits"]
        assert run_request(reopened, "GET", "/api/v1/habits/1/check-ins", headers=reopened_headers).json()[0]["status"] == "completed"
    elif scenario == "terminal-states":
        assert run_request(reopened, "GET", "/api/v1/tasks", headers=reopened_headers).json()[0]["status"] == "archived"
    elif scenario == "two-users":
        other_login = run_request(reopened, "POST", "/api/v1/auth/login", json={"username": "other", "password": "other-pass"})
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
        assert run_request(reopened, "GET", "/api/v1/inbox", headers=other_headers).json() == []
    elif scenario == "rollback":
        assert run_request(reopened, "GET", "/api/v1/tasks", headers=reopened_headers).json() == []
    elif scenario == "migration-repeat":
        assert run_request(reopened, "GET", "/api/v1/projects", headers=reopened_headers).status_code == 200
    else:
        assert run_request(reopened, "GET", "/api/v1/today?date=2026-07-01", headers=reopened_headers).status_code == 200
    close_owned_app(reopened)


def test_root_owned_connection_is_closed_after_real_lifespan(tmp_path):
    path = tmp_path / "owned.sqlite3"
    app = setup_app(path)

    async def close_app():
        async with app.router.lifespan_context(app):
            assert app.state.internal_api.connection
    asyncio.run(close_app())
    with pytest.raises(Exception):
        app.state.internal_api.connection.execute("SELECT 1")
