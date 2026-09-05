"""Contract-field and failure-atomicity matrices for InternalAPI."""

from datetime import date
from dataclasses import FrozenInstanceError

import pytest

from openipe.api.internal.contracts import (
    GoalCreateContract, GoalUpdateContract, HabitCreateContract, HabitUpdateContract,
    InboxCreateContract, InboxUpdateContract, ProjectCreateContract, ProjectUpdateContract,
    StackCreateContract, StackUpdateContract, TaskCreateContract, TaskUpdateContract,
)
from openipe.api.internal.errors import InternalNotFoundError, InternalValidationError
from openipe.core.models.habit import HabitFrequencyType
from openipe.core.models.task import TaskPriority, TaskStatus
from tests.internal_support import admin, make_internal


@pytest.mark.parametrize("resource", ["inbox", "goal", "project", "task", "habit", "stack"], ids=["inbox", "goal", "project", "task", "habit", "stack"])
def test_each_create_contract_produces_the_expected_public_shape(tmp_path, resource):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        values = {
            "inbox": api.inbox.create(context, InboxCreateContract("contract idea")),
            "goal": api.goals.create(context, GoalCreateContract("contract goal", "description", date(2026, 8, 1))),
            "project": api.projects.create(context, ProjectCreateContract("contract project", "description")),
            "task": api.tasks.create(context, TaskCreateContract("contract task", "description", None, TaskPriority.HIGH, date(2026, 8, 1), True)),
            "habit": api.habits.create(context, HabitCreateContract("contract habit", "description", HabitFrequencyType.DAILY, {}, "v1")),
            "stack": api.habit_stacks.create(context, StackCreateContract("contract stack", "description")),
        }
        result = values[resource]
        assert result.id > 0
        assert result.__class__.__module__ == "openipe.api.internal.contracts"
    finally:
        connection.close()


@pytest.mark.parametrize(
    "resource,field,value",
    [
        pytest.param("task", "title", "renamed", id="task-title"),
        pytest.param("task", "description", "new description", id="task-description"),
        pytest.param("task", "priority", TaskPriority.HIGH, id="task-priority"),
        pytest.param("task", "due_date", date(2026, 9, 1), id="task-due-date"),
        pytest.param("task", "is_today", True, id="task-today"),
        pytest.param("project", "title", "renamed", id="project-title"),
        pytest.param("project", "description", "new description", id="project-description"),
        pytest.param("goal", "title", "renamed", id="goal-title"),
        pytest.param("goal", "description", "new description", id="goal-description"),
        pytest.param("goal", "target_date", date(2026, 9, 1), id="goal-target-date"),
        pytest.param("habit", "title", "renamed", id="habit-title"),
        pytest.param("habit", "description", "new description", id="habit-description"),
        pytest.param("habit", "minimum_version", "v2", id="habit-minimum-version"),
        pytest.param("stack", "name", "renamed", id="stack-name"),
        pytest.param("stack", "description", "new description", id="stack-description"),
        pytest.param("stack", "active", False, id="stack-active"),
    ],
)
def test_update_fields_are_independently_observable(tmp_path, resource, field, value):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        records = {
            "task": api.tasks.create(context, "task"),
            "project": api.projects.create(context, "project"),
            "goal": api.goals.create(context, "goal"),
            "habit": api.habits.create(context, "habit"),
            "stack": api.habit_stacks.create(context, "stack"),
        }
        record = records[resource]
        result = getattr(api, resource + "s" if resource not in {"goal", "habit", "stack"} else {"goal": "goals", "habit": "habits", "stack": "habit_stacks"}[resource]).update(context, record.id, **{field: value})
        assert getattr(result, field) == value
    finally:
        connection.close()


@pytest.mark.parametrize(
    "failure",
    [
        pytest.param("missing-inbox", id="missing-inbox"),
        pytest.param("missing-goal", id="missing-goal"),
        pytest.param("missing-project", id="missing-project"),
        pytest.param("missing-task", id="missing-task"),
        pytest.param("missing-habit", id="missing-habit"),
        pytest.param("missing-stack", id="missing-stack"),
        pytest.param("bad-project-assignment", id="bad-project-assignment"),
        pytest.param("bad-next-action", id="bad-next-action"),
        pytest.param("bad-association", id="bad-association"),
        pytest.param("bad-reorder", id="bad-reorder"),
        pytest.param("bad-checkin-delete", id="bad-checkin-delete"),
        pytest.param("bad-schedule", id="bad-schedule"),
    ],
)
def test_failed_internal_operation_leaves_public_state_unchanged(tmp_path, failure):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        inbox = api.inbox.create(context, "stable")
        goal = api.goals.create(context, "stable goal")
        project = api.projects.create(context, "stable project")
        task = api.tasks.create(context, "stable task", project_id=project.id)
        habit = api.habits.create(context, "stable habit")
        stack = api.habit_stacks.create(context, "stable stack")
        before = (api.inbox.get(context, inbox.id), api.goals.get(context, goal.id), api.projects.get(context, project.id), api.tasks.get(context, task.id), api.habits.get(context, habit.id), api.habit_stacks.get(context, stack.id))
        with pytest.raises((InternalNotFoundError, InternalValidationError)):
            if failure == "missing-inbox": api.inbox.get(context, 99999)
            elif failure == "missing-goal": api.goals.get(context, 99999)
            elif failure == "missing-project": api.projects.get(context, 99999)
            elif failure == "missing-task": api.tasks.get(context, 99999)
            elif failure == "missing-habit": api.habits.get(context, 99999)
            elif failure == "missing-stack": api.habit_stacks.get(context, 99999)
            elif failure == "bad-project-assignment": api.tasks.update(context, task.id, project_id=99999)
            elif failure == "bad-next-action": api.projects.set_next_action(context, project.id, 99999)
            elif failure == "bad-association": api.goals.associate(context, goal.id, 99999, "task")
            elif failure == "bad-reorder": api.habit_stacks.reorder_stacks(context, [99999])
            elif failure == "bad-checkin-delete": api.habits.delete_check_in(context, habit.id, date(2026, 10, 1))
            else: api.habits.create(context, "bad", frequency_type=HabitFrequencyType.SELECTED_DAYS, frequency_config={"days": []})
        after = (api.inbox.get(context, inbox.id), api.goals.get(context, goal.id), api.projects.get(context, project.id), api.tasks.get(context, task.id), api.habits.get(context, habit.id), api.habit_stacks.get(context, stack.id))
        assert before == after
    finally:
        connection.close()


@pytest.mark.parametrize("field", ["id", "title", "description", "status", "created_at", "updated_at", "archived_at", "source_inbox_item_id"], ids=["id", "title", "description", "status", "created", "updated", "archived", "source"])
def test_public_project_contracts_are_immutable_for_every_core_field(tmp_path, field):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        project = api.projects.create(context, "immutable")
        with pytest.raises(FrozenInstanceError):
            setattr(project, field, getattr(project, field))
    finally:
        connection.close()
