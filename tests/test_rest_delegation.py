import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest

from openipe.api.REST.app import create_app
from openipe.api.internal import InternalContext
from openipe.api.internal.contracts import (
    CheckInContract, GoalContract, GoalEvidenceContract, InboxContract, LoginContract,
    ProjectContract, TaskContract, TodayCompletedContract, TodayContract, UserContract,
)
from openipe.api.internal.contracts import GoalStatus, HabitCheckInStatus, TaskPriority, TaskStatus, ProjectStatus
from openipe.core.models.user import User


def _user_contract():
    now = datetime.now(timezone.utc)
    return UserContract(1, "admin", "Admin", True, True, now, now, now)


class SpyAPI:
    def __init__(self):
        self.calls = []
        self.context = InternalContext(User(1, "admin", "Admin", "ignored", True, True, datetime.now(timezone.utc), datetime.now(timezone.utc), None))
        self.auth = SimpleNamespace(
            initial_admin=self.initial_admin,
            login=self.login,
            logout=lambda token: None,
            current_user=lambda context: _user_contract(),
            change_password=lambda *args: None,
        )
        self.users = SimpleNamespace(list=lambda context: [], create=self.create_user, get=lambda *args: _user_contract(), update=lambda *args: _user_contract())
        self.inbox = SimpleNamespace(create=self.create_inbox, list=lambda *args: [], get=lambda *args: self.create_inbox(None, "x"), update=lambda *args: self.create_inbox(None, "x"), delete=lambda *args: None)
        self.goals = SimpleNamespace(associate=self.associate, list=lambda *args: [], create=lambda *args: None, get=lambda *args: None)
        self.projects = SimpleNamespace(list=lambda *args: [], create=self.create_project, get=lambda *args: None, set_next_action=self.set_next_action)
        self.tasks = SimpleNamespace(list=lambda *args: [], create=self.create_task, get=lambda *args: None)
        self.habits = SimpleNamespace(check_in=self.check_in, list=lambda *args: [], create=lambda *args: None)
        self.habit_stacks = SimpleNamespace(reorder_stacks=self.reorder_stacks, list=lambda *args: [])
        self.today = SimpleNamespace(get=self.get_today)

    def authenticate(self, token):
        self.calls.append(("authenticate", token))
        return self.context

    def authorize_admin(self, context):
        self.calls.append(("authorize_admin", context))
        return context

    def initial_admin(self, request):
        self.calls.append(("initial_admin", request))
        return _user_contract()

    def login(self, request):
        self.calls.append(("login", request))
        return LoginContract("token", datetime.now(timezone.utc), _user_contract())

    def create_user(self, context, request):
        self.calls.append(("create_user", context, request))
        return _user_contract()

    def create_inbox(self, context, text):
        self.calls.append(("create_inbox", context, text))
        text = text.text if hasattr(text, "text") else text
        now = datetime.now(timezone.utc)
        from openipe.api.internal.contracts import InboxStatus
        return InboxContract(1, text or "x", InboxStatus.UNPROCESSED, now, now, None, None)

    def associate(self, context, goal_id, related_id, kind):
        self.calls.append(("associate", context, goal_id, related_id, kind))
        now = datetime.now(timezone.utc)
        return GoalContract(goal_id, "Goal", None, GoalStatus.ACTIVE, None, now, now, None, None, None, [related_id], [], [], GoalEvidenceContract(1, 0, 0, 0, 0, 0, 0))

    def create_project(self, *args):
        self.calls.append(("create_project", args))
        now = datetime.now(timezone.utc)
        return ProjectContract(1, "Project", None, ProjectStatus.ACTIVE, None, None, now, now, None, None, [], 0, 0, 0)

    def set_next_action(self, *args):
        self.calls.append(("set_next_action", args))
        return self.create_project(*args)

    def create_task(self, *args):
        self.calls.append(("create_task", args))
        now = datetime.now(timezone.utc)
        return TaskContract(1, "Task", None, None, TaskStatus.OPEN, TaskPriority.NORMAL, None, False, None, now, now, None, None)

    def check_in(self, *args):
        self.calls.append(("check_in", args))
        now = datetime.now(timezone.utc)
        return CheckInContract(1, 1, datetime.now(timezone.utc).date(), HabitCheckInStatus.COMPLETED, None, now, now)

    def reorder_stacks(self, *args):
        self.calls.append(("reorder_stacks", args))

    def get_today(self, *args):
        self.calls.append(("today", args))
        return TodayContract(datetime.now(timezone.utc).date(), [], [], [], TodayCompletedContract([], []))


async def _client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def test_representative_rest_routes_delegate_to_injected_facade():
    spy = SpyAPI()
    app = create_app(spy)
    async def exercise():
        async with await _client(app) as client:
            assert (await client.post("/api/v1/setup/initial-admin", json={"username": "a", "display_name": "A", "password": "password"})).status_code == 201
            assert (await client.post("/api/v1/auth/login", json={"username": "a", "password": "password"})).status_code == 200
            headers = {"Authorization": "Bearer token"}
            assert (await client.post("/api/v1/inbox", headers=headers, json={"text": "idea"})).status_code == 201
            assert (await client.post("/api/v1/users", headers=headers, json={"username": "u", "display_name": "U", "password": "password"})).status_code == 201
            assert (await client.post("/api/v1/goals/1/projects/2", headers=headers)).status_code == 200
            assert (await client.post("/api/v1/projects", headers=headers, json={"title": "Project"})).status_code == 201
            assert (await client.post("/api/v1/tasks", headers=headers, json={"title": "Task"})).status_code == 201
            assert (await client.post("/api/v1/habits/1/check-ins", headers=headers, json={"date": "2026-01-01"})).status_code == 200
            assert (await client.post("/api/v1/habit-stacks/reorder", headers=headers, json={"ids": []})).status_code == 204
            assert (await client.get("/api/v1/today", headers=headers)).status_code == 200
    asyncio.run(exercise())
    names = [call[0] for call in spy.calls]
    assert {"initial_admin", "login", "authenticate", "authorize_admin", "create_inbox", "create_user", "associate", "create_project", "create_task", "check_in", "reorder_stacks", "today"} <= set(names)
    assert any(call[0] == "authenticate" and call[1] == "token" for call in spy.calls)
    assert any(call[0] == "authorize_admin" and call[1] is spy.context for call in spy.calls)
    assert any(call[0] == "create_inbox" and call[1] is spy.context and call[2].text == "idea" for call in spy.calls)
    assert any(call[0] == "create_user" and call[1] is spy.context and call[2].username == "u" for call in spy.calls)
    assert any(call[0] == "associate" and call[1] is spy.context and call[2:] == (1, 2, "project") for call in spy.calls)
    assert any(call[0] == "create_project" and call[1][1].title == "Project" for call in spy.calls)
    assert any(call[0] == "create_task" and call[1][1].title == "Task" for call in spy.calls)
    assert any(call[0] == "check_in" and call[1][0] is spy.context and call[1][2].date.isoformat() == "2026-01-01" for call in spy.calls)
    assert any(call[0] == "reorder_stacks" and call[1][1].ids == () for call in spy.calls)
    assert any(call[0] == "today" and call[1][1].include_completed is False for call in spy.calls)
