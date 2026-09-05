"""Direct SQLite/repository invariants complementing service-level tests."""

import sqlite3
from datetime import date

import pytest

from openipe.api.internal import InternalAPI
from openipe.core.config import Settings
from openipe.core.models.habit import HabitFrequencyType
from openipe.core.models.task import TaskPriority, TaskStatus
from openipe.core.security import hash_password
from openipe.persistence.database import initialize_database
from openipe.persistence.repositories.goal_association_repository import GoalAssociationRepository
from openipe.persistence.repositories.goal_repository import GoalRepository
from openipe.persistence.repositories.habit_repository import HabitRepository
from openipe.persistence.repositories.habit_stack_repository import HabitStackRepository
from openipe.persistence.repositories.inbox_repository import InboxRepository
from openipe.persistence.repositories.project_repository import ProjectRepository
from openipe.persistence.repositories.task_repository import TaskRepository
from openipe.persistence.repositories.user_repository import AuthTokenRepository, UserRepository
from tests.internal_support import admin


def seed(tmp_path):
    path = tmp_path / "repository.sqlite3"
    connection = initialize_database(path)
    api = InternalAPI(connection, Settings(database_path=path))
    _, context = admin(api)
    return path, connection, api, context


@pytest.mark.parametrize(
    "repository",
    ["users", "inbox", "goals", "projects", "tasks", "habits", "stacks", "associations", "tokens"],
    ids=["users", "inbox", "goals", "projects", "tasks", "habits", "stacks", "associations", "tokens"],
)
def test_repository_records_are_scoped_by_exact_owner(tmp_path, repository):
    path, connection, api, context = seed(tmp_path)
    try:
        api.users.create(context, "other", "Other", "other-pass")
        other = api.authenticate(api.auth.login("other", "other-pass").access_token)
        inbox = api.inbox.create(context, "private")
        goal = api.goals.create(context, "goal")
        project = api.projects.create(context, "project")
        task = api.tasks.create(context, "task", project_id=project.id)
        habit = api.habits.create(context, "habit")
        stack = api.habit_stacks.create(context, "stack")
        records = {
            "users": lambda: api.users.get(other, context.actor.id),
            "inbox": lambda: api.inbox.get(other, inbox.id),
            "goals": lambda: api.goals.get(other, goal.id),
            "projects": lambda: api.projects.get(other, project.id),
            "tasks": lambda: api.tasks.get(other, task.id),
            "habits": lambda: api.habits.get(other, habit.id),
            "stacks": lambda: api.habit_stacks.get(other, stack.id),
            "associations": lambda: api.goals.associated_ids(other, goal.id),
            "tokens": lambda: api.authenticate(api.auth.login("admin", "admin-pass").access_token),
        }
        if repository == "tokens":
            assert records[repository]() is not None
        else:
            with pytest.raises(Exception):
                records[repository]()
    finally:
        connection.close()


@pytest.mark.parametrize("kind", ["project", "task", "habit"], ids=["project", "task", "habit"])
def test_goal_association_repository_is_idempotent_and_ordered(tmp_path, kind):
    path, connection, api, context = seed(tmp_path)
    try:
        goal = api.goals.create(context, "goal")
        related = {
            "project": api.projects.create(context, "p").id,
            "task": api.tasks.create(context, "t").id,
            "habit": api.habits.create(context, "h").id,
        }[kind]
        repository = GoalAssociationRepository(connection)
        repository.add(kind, goal.id, related)
        repository.add(kind, goal.id, related)
        assert repository.ids(kind, goal.id) == [related]
        assert repository.goal_ids_for_related(kind, related) == [goal.id]
        repository.remove(kind, goal.id, related)
        assert repository.ids(kind, goal.id) == []
    finally:
        connection.close()


@pytest.mark.parametrize("kind", ["project", "task", "habit"], ids=["project", "task", "habit"])
def test_foreign_key_cascade_removes_goal_associations(tmp_path, kind):
    path, connection, api, context = seed(tmp_path)
    try:
        goal = api.goals.create(context, "goal")
        related = {
            "project": api.projects.create(context, "p").id,
            "task": api.tasks.create(context, "t").id,
            "habit": api.habits.create(context, "h").id,
        }[kind]
        association = GoalAssociationRepository(connection)
        association.add(kind, goal.id, related)
        connection.execute("DELETE FROM goals WHERE id = ?", (goal.id,))
        connection.commit()
        assert association.goal_ids_for_related(kind, related) == []
    finally:
        connection.close()


@pytest.mark.parametrize(
    "factory",
    ["inbox", "goal", "project", "task", "habit", "stack", "token"],
    ids=["inbox-null", "goal-null", "project-null", "task-null", "habit-null", "stack-null", "token"],
)
def test_repository_nullable_columns_round_trip(tmp_path, factory):
    path, connection, api, context = seed(tmp_path)
    try:
        if factory == "inbox":
            item = api.inbox.create(context, "nullable")
            row = InboxRepository(connection).get(context.actor.id, item.id)
            assert row.processed_at is None and row.archived_at is None
        elif factory == "goal":
            goal = api.goals.create(context, "nullable")
            assert GoalRepository(connection).get(context.actor.id, goal.id).description is None
        elif factory == "project":
            project = api.projects.create(context, "nullable")
            assert ProjectRepository(connection).get(context.actor.id, project.id).description is None
        elif factory == "task":
            task = api.tasks.create(context, "nullable")
            row = TaskRepository(connection).get(context.actor.id, task.id)
            assert row.description is None and row.due_date is None
        elif factory == "habit":
            habit = api.habits.create(context, "nullable", frequency_type=HabitFrequencyType.DAILY)
            assert HabitRepository(connection).get(context.actor.id, habit.id).minimum_version is None
        elif factory == "stack":
            stack = api.habit_stacks.create(context, "nullable")
            assert HabitStackRepository(connection).get(context.actor.id, stack.id).description is None
        else:
            token = api.auth.login("admin", "admin-pass")
            assert connection.execute("SELECT revoked_at FROM auth_tokens WHERE token_hash IS NOT NULL").fetchone()[0] is None
            assert token.access_token
    finally:
        connection.close()


@pytest.mark.parametrize("status", ["open", "completed", "cancelled", "archived"], ids=["open", "completed", "cancelled", "archived"])
def test_task_repository_status_filter_is_exact(tmp_path, status):
    path, connection, api, context = seed(tmp_path)
    try:
        task = api.tasks.create(context, "task")
        if status == "completed": api.tasks.complete(context, task.id)
        if status == "cancelled": api.tasks.cancel(context, task.id)
        if status == "archived": api.tasks.update(context, task.id, status=TaskStatus.ARCHIVED)
        result = TaskRepository(connection).list(context.actor.id, status=TaskStatus(status))
        assert result and all(item.status.value == status for item in result)
    finally:
        connection.close()


@pytest.mark.parametrize("active", [None, True, False], ids=["all", "active", "inactive"])
def test_habit_and_stack_active_filters_are_exact(tmp_path, active):
    path, connection, api, context = seed(tmp_path)
    try:
        habit = api.habits.create(context, "habit")
        stack = api.habit_stacks.create(context, "stack")
        api.habits.deactivate(context, habit.id)
        api.habit_stacks.archive(context, stack.id)
        habits = HabitRepository(connection).list(context.actor.id, active)
        stacks = HabitStackRepository(connection).list(context.actor.id, active)
        if active is None:
            assert len(habits) == 1 and len(stacks) == 1
        elif active:
            assert habits == [] and stacks == []
        else:
            assert len(habits) == 1 and len(stacks) == 1
    finally:
        connection.close()


@pytest.mark.parametrize("table", ["users", "inbox_items", "goals", "projects", "tasks", "habits", "habit_stacks"], ids=["users", "inbox", "goals", "projects", "tasks", "habits", "stacks"])
def test_foreign_keys_reject_invalid_parent_ids(tmp_path, table):
    path, connection, api, context = seed(tmp_path)
    try:
        statements = {
            "users": "INSERT INTO auth_tokens(user_id, token_hash, created_at, expires_at) VALUES (999, 'x', 'x', 'x')",
            "inbox_items": "INSERT INTO inbox_items(user_id, text, status, created_at, updated_at) VALUES (999, 'x', 'unprocessed', 'x', 'x')",
            "goals": "INSERT INTO goals(user_id, title, status, created_at, updated_at) VALUES (999, 'x', 'active', 'x', 'x')",
            "projects": "INSERT INTO projects(user_id, title, status, created_at, updated_at) VALUES (999, 'x', 'active', 'x', 'x')",
            "tasks": "INSERT INTO tasks(user_id, title, status, priority, created_at, updated_at) VALUES (999, 'x', 'open', 'normal', 'x', 'x')",
            "habits": "INSERT INTO habits(user_id, title, frequency_type, frequency_config, created_at, updated_at) VALUES (999, 'x', 'daily', '{}', 'x', 'x')",
            "habit_stacks": "INSERT INTO habit_stacks(user_id, name, created_at, updated_at) VALUES (999, 'x', 'x', 'x')",
        }
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(statements[table])
        connection.rollback()
    finally:
        connection.close()


@pytest.mark.parametrize("repository", ["users", "inbox", "goals", "projects", "tasks", "habits", "stacks"], ids=["users", "inbox", "goals", "projects", "tasks", "habits", "stacks"])
def test_committed_repository_state_is_visible_to_second_connection(tmp_path, repository):
    path, connection, api, context = seed(tmp_path)
    second = initialize_database(path)
    try:
        values = {
            "users": api.users.list(context),
            "inbox": [api.inbox.create(context, "visible")],
            "goals": [api.goals.create(context, "visible")],
            "projects": [api.projects.create(context, "visible")],
            "tasks": [api.tasks.create(context, "visible")],
            "habits": [api.habits.create(context, "visible")],
            "stacks": [api.habit_stacks.create(context, "visible")],
        }
        table = {"users": "users", "inbox": "inbox_items", "goals": "goals", "projects": "projects", "tasks": "tasks", "habits": "habits", "stacks": "habit_stacks"}[repository]
        assert second.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] >= len(values[repository])
    finally:
        second.close()
        connection.close()
