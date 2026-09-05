"""Deterministic lifecycle and invariant matrices for connected resources."""

from datetime import date

import pytest

from openipe.api.internal.errors import InternalValidationError
from openipe.core.models.goal import GoalStatus
from openipe.core.models.project import ProjectStatus
from openipe.core.models.task import TaskStatus
from tests.internal_support import admin, make_internal


@pytest.mark.parametrize(
    "start,action,expected",
    [
        pytest.param(GoalStatus.ACTIVE, "pause", GoalStatus.PAUSED, id="active-pause"),
        pytest.param(GoalStatus.ACTIVE, "achieve", GoalStatus.ACHIEVED, id="active-achieve"),
        pytest.param(GoalStatus.ACTIVE, "abandon", GoalStatus.ABANDONED, id="active-abandon"),
        pytest.param(GoalStatus.ACTIVE, "archive", GoalStatus.ARCHIVED, id="active-archive"),
        pytest.param(GoalStatus.PAUSED, "resume", GoalStatus.ACTIVE, id="paused-resume"),
        pytest.param(GoalStatus.PAUSED, "achieve", GoalStatus.ACHIEVED, id="paused-achieve"),
        pytest.param(GoalStatus.PAUSED, "abandon", GoalStatus.ABANDONED, id="paused-abandon"),
        pytest.param(GoalStatus.ACHIEVED, "resume", None, id="achieved-resume-invalid"),
        pytest.param(GoalStatus.ABANDONED, "pause", None, id="abandoned-pause-invalid"),
        pytest.param(GoalStatus.ARCHIVED, "resume", None, id="archived-resume-invalid"),
    ],
)
def test_goal_state_machine_is_atomic(tmp_path, start, action, expected):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        goal = api.goals.create(context, "goal")
        if start is GoalStatus.PAUSED:
            api.goals.pause(context, goal.id)
        elif start is GoalStatus.ACHIEVED:
            api.goals.achieve(context, goal.id)
        elif start is GoalStatus.ABANDONED:
            api.goals.abandon(context, goal.id)
        elif start is GoalStatus.ARCHIVED:
            api.goals.archive(context, goal.id)
        before = api.goals.get(context, goal.id)
        if expected is None:
            with pytest.raises(InternalValidationError):
                getattr(api.goals, action)(context, goal.id)
            assert api.goals.get(context, goal.id).status is before.status
        else:
            assert getattr(api.goals, action)(context, goal.id).status is expected
    finally:
        connection.close()


@pytest.mark.parametrize(
    "start,action,expected",
    [
        pytest.param(ProjectStatus.ACTIVE, "pause", ProjectStatus.PAUSED, id="active-pause"),
        pytest.param(ProjectStatus.ACTIVE, "complete", ProjectStatus.COMPLETED, id="active-complete"),
        pytest.param(ProjectStatus.ACTIVE, "cancel", ProjectStatus.CANCELLED, id="active-cancel"),
        pytest.param(ProjectStatus.ACTIVE, "archive", ProjectStatus.ARCHIVED, id="active-archive"),
        pytest.param(ProjectStatus.PAUSED, "resume", ProjectStatus.ACTIVE, id="paused-resume"),
        pytest.param(ProjectStatus.PAUSED, "complete", ProjectStatus.COMPLETED, id="paused-complete"),
        pytest.param(ProjectStatus.COMPLETED, "resume", None, id="completed-resume-invalid"),
        pytest.param(ProjectStatus.CANCELLED, "complete", None, id="cancelled-complete-invalid"),
        pytest.param(ProjectStatus.ARCHIVED, "cancel", None, id="archived-cancel-invalid"),
    ],
)
def test_project_state_machine_is_atomic(tmp_path, start, action, expected):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        project = api.projects.create(context, "project")
        if start is ProjectStatus.PAUSED: api.projects.pause(context, project.id)
        if start is ProjectStatus.COMPLETED: api.projects.complete(context, project.id)
        if start is ProjectStatus.CANCELLED: api.projects.cancel(context, project.id)
        if start is ProjectStatus.ARCHIVED: api.projects.archive(context, project.id)
        before = api.projects.get(context, project.id)
        if expected is None:
            with pytest.raises(InternalValidationError): getattr(api.projects, action)(context, project.id)
            assert api.projects.get(context, project.id).status is before.status
        else:
            assert getattr(api.projects, action)(context, project.id).status is expected
    finally:
        connection.close()


@pytest.mark.parametrize(
    "start,action,expected",
    [
        pytest.param(TaskStatus.OPEN, "complete", TaskStatus.COMPLETED, id="open-complete"),
        pytest.param(TaskStatus.OPEN, "cancel", TaskStatus.CANCELLED, id="open-cancel"),
        pytest.param(TaskStatus.COMPLETED, "reopen", TaskStatus.OPEN, id="completed-reopen"),
        pytest.param(TaskStatus.COMPLETED, "complete", None, id="completed-complete-invalid"),
        pytest.param(TaskStatus.CANCELLED, "complete", None, id="cancelled-complete-invalid"),
        pytest.param(TaskStatus.CANCELLED, "reopen", None, id="cancelled-reopen-invalid"),
        pytest.param(TaskStatus.ARCHIVED, "reopen", None, id="archived-reopen-invalid"),
    ],
)
def test_task_state_machine_preserves_failed_state(tmp_path, start, action, expected):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        task = api.tasks.create(context, "task")
        if start is TaskStatus.COMPLETED: api.tasks.complete(context, task.id)
        if start is TaskStatus.CANCELLED: api.tasks.cancel(context, task.id)
        if start is TaskStatus.ARCHIVED: api.tasks.update(context, task.id, status=TaskStatus.ARCHIVED)
        before = api.tasks.get(context, task.id)
        if expected is None:
            with pytest.raises(InternalValidationError): getattr(api.tasks, action)(context, task.id)
            assert api.tasks.get(context, task.id).status is before.status
        else:
            assert getattr(api.tasks, action)(context, task.id).status is expected
    finally:
        connection.close()


@pytest.mark.parametrize("selected", [date(2026, 1, day) for day in range(1, 8)], ids=[f"day-{day}" for day in range(1, 8)])
def test_today_progress_counts_remain_bounded_for_every_weekday(tmp_path, selected):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        habit = api.habits.create(context, "daily")
        stack = api.habit_stacks.create(context, "stack")
        api.habit_stacks.add_habit(context, stack.id, habit.id)
        progress = api.habit_stacks.progress(context, stack.id, selected)
        assert 0 <= progress[0] <= progress[1]
        api.habits.check_in(context, habit.id, selected)
        progress = api.habit_stacks.progress(context, stack.id, selected)
        assert 0 <= progress[0] <= progress[1]
    finally:
        connection.close()


@pytest.mark.parametrize("action", ["activate", "deactivate", "archive"], ids=["activate", "deactivate", "archive"])
def test_habit_lifecycle_repeated_operations_keep_public_state_coherent(tmp_path, action):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        habit = api.habits.create(context, "habit")
        result = getattr(api.habits, action)(context, habit.id)
        repeated = getattr(api.habits, action)(context, habit.id)
        assert result.id == repeated.id and repeated.active is (action == "activate")
    finally:
        connection.close()


@pytest.mark.parametrize("action", ["archive", "add_habit", "remove_habit", "reorder_stacks"], ids=["archive", "add", "remove", "reorder"])
def test_stack_operations_keep_progress_non_negative(tmp_path, action):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        stack = api.habit_stacks.create(context, "stack")
        habit = api.habits.create(context, "habit")
        if action == "archive":
            result = api.habit_stacks.archive(context, stack.id)
            assert result.active is False
        elif action == "add_habit":
            result = api.habit_stacks.add_habit(context, stack.id, habit.id)
            assert result.habits[0].id == habit.id
        elif action == "remove_habit":
            api.habit_stacks.add_habit(context, stack.id, habit.id)
            result = api.habit_stacks.remove_habit(context, stack.id, habit.id)
            assert result.habits == []
        else:
            api.habit_stacks.reorder_stacks(context, [stack.id])
            result = api.habit_stacks.progress(context, stack.id)
            assert 0 <= result[0] <= result[1]
    finally:
        connection.close()
