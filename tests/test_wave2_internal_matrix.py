"""Wave 2 parameter matrices for the transport-independent API.

Each parameter is a distinct business input or state boundary.  The tests use
fresh temporary SQLite databases so a failed case cannot contaminate another.
"""

from datetime import date

import pytest

from openipe.api.internal.contracts import (
    CheckInCreateContract,
    GoalCreateContract,
    HabitCreateContract,
    InboxCreateContract,
    ProjectCreateContract,
    ReorderContract,
    StackCreateContract,
    TaskCreateContract,
    TodayQueryContract,
    UserCreateContract,
)
from openipe.api.internal.errors import (
    InternalAuthenticationError,
    InternalNotFoundError,
    InternalValidationError,
)
from openipe.core.models.goal import GoalStatus
from openipe.core.models.habit import HabitCheckInStatus, HabitFrequencyType
from openipe.core.models.inbox import InboxStatus
from openipe.core.models.project import ProjectStatus
from openipe.core.models.task import TaskPriority, TaskStatus
from tests.internal_support import admin, make_internal


INBOX_TEXTS = [
    pytest.param("simple idea", "simple idea", id="plain"),
    pytest.param("  surrounding whitespace  ", "surrounding whitespace", id="trimmed"),
    pytest.param("emoji 🚀", "emoji 🚀", id="emoji"),
    pytest.param("e\u0301 combining", "e\u0301 combining", id="combining-character"),
    pytest.param("line one\nline two", "line one\nline two", id="multiline"),
    pytest.param("quotes ' \" and punctuation !?", "quotes ' \" and punctuation !?", id="punctuation"),
    pytest.param("SELECT * FROM users;", "SELECT * FROM users;", id="sql-like"),
    pytest.param('{"idea": [1, true]}', '{"idea": [1, true]}', id="json-like"),
    pytest.param("duplicate", "duplicate", id="duplicate-first"),
    pytest.param("duplicate", "duplicate", id="duplicate-second"),
    pytest.param("x" * 512, "x" * 512, id="long-value"),
    pytest.param("tabs\tand\r\nnewlines", "tabs\tand\r\nnewlines", id="control-whitespace"),
]


@pytest.mark.parametrize("raw,expected", INBOX_TEXTS)
def test_internal_inbox_accepts_and_normalizes_meaningful_text(tmp_path, raw, expected):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        item = api.inbox.create(context, InboxCreateContract(raw))
        assert item.text == expected
        assert item.status == InboxStatus.UNPROCESSED
        assert item.id in [x.id for x in api.inbox.list(context)]
    finally:
        connection.close()


@pytest.mark.parametrize(
    "raw",
    ["", " ", "\t", "\n", "\r\n"],
    ids=["empty", "space", "tab", "newline", "crlf"],
)
def test_internal_inbox_rejects_empty_text_without_mutation(tmp_path, raw):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        with pytest.raises(InternalValidationError):
            api.inbox.create(context, raw)
        assert api.inbox.list(context) == []
    finally:
        connection.close()


@pytest.mark.parametrize(
    "operation,expected",
    [
        pytest.param("process", InboxStatus.PROCESSED, id="process"),
        pytest.param("archive", InboxStatus.ARCHIVED, id="archive"),
        pytest.param("discard", InboxStatus.DISCARDED, id="discard"),
    ],
)
def test_internal_inbox_lifecycle_helpers_are_repeatable(tmp_path, operation, expected):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        item = api.inbox.create(context, "workflow")
        first = getattr(api.inbox, operation)(context, item.id)
        second = getattr(api.inbox, operation)(context, item.id)
        assert first.status == expected
        assert second.status == expected
        assert api.inbox.get(context, item.id).status == expected
    finally:
        connection.close()


@pytest.mark.parametrize(
    "status",
    [InboxStatus.UNPROCESSED, InboxStatus.PROCESSED, InboxStatus.ARCHIVED, InboxStatus.DISCARDED],
    ids=["unprocessed", "processed", "archived", "discarded"],
)
def test_internal_inbox_status_filter_returns_only_requested_state(tmp_path, status):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        item = api.inbox.create(context, "filter")
        if status != InboxStatus.UNPROCESSED:
            getattr(api.inbox, {InboxStatus.PROCESSED: "process", InboxStatus.ARCHIVED: "archive", InboxStatus.DISCARDED: "discard"}[status])(context, item.id)
        result = api.inbox.list(context, status)
        assert result and all(x.status == status for x in result)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "priority",
    [TaskPriority.LOW, TaskPriority.NORMAL, TaskPriority.HIGH],
    ids=["low", "normal", "high"],
)
def test_internal_task_priority_round_trips_as_enum(tmp_path, priority):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        task = api.tasks.create(context, TaskCreateContract("priority", priority=priority))
        assert task.priority is priority
        assert api.tasks.get(context, task.id).priority is priority
    finally:
        connection.close()


@pytest.mark.parametrize(
    "status",
    [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.ARCHIVED],
    ids=["completed", "cancelled", "archived"],
)
def test_internal_task_terminal_states_clear_or_preserve_expected_fields(tmp_path, status):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        task = api.tasks.create(context, "terminal", is_today=True)
        if status is TaskStatus.COMPLETED:
            result = api.tasks.complete(context, task.id)
        elif status is TaskStatus.CANCELLED:
            result = api.tasks.cancel(context, task.id)
        else:
            result = api.tasks.update(context, task.id, status=TaskStatus.ARCHIVED)
        assert result.status is status
        with pytest.raises(InternalValidationError):
            api.tasks.complete(context, task.id)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "action",
    ["pause", "achieve", "abandon", "archive"],
    ids=["pause", "achieve", "abandon", "archive"],
)
def test_internal_goal_lifecycle_dispatch_has_no_partial_mutation(tmp_path, action):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        goal = api.goals.create(context, GoalCreateContract("goal", target_date=date(2026, 2, 1)))
        result = api.goals.lifecycle(context, goal.id, action)
        assert result.status.value == {"pause": "paused", "achieve": "achieved", "abandon": "abandoned", "archive": "archived"}[action]
        if action == "pause":
            assert api.goals.resume(context, goal.id).status is GoalStatus.ACTIVE
        else:
            with pytest.raises(InternalValidationError):
                api.goals.resume(context, goal.id)
        expected_status = GoalStatus.ACTIVE if action == "pause" else result.status
        assert api.goals.get(context, goal.id).status is expected_status
    finally:
        connection.close()


@pytest.mark.parametrize(
    "kind",
    ["project", "task", "habit"],
    ids=["project", "task", "habit"],
)
def test_goal_association_kinds_are_idempotent_and_removable(tmp_path, kind):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        goal = api.goals.create(context, "goal")
        target = {
            "project": api.projects.create(context, ProjectCreateContract("project")).id,
            "task": api.tasks.create(context, TaskCreateContract("task")).id,
            "habit": api.habits.create(context, HabitCreateContract("habit")).id,
        }[kind]
        api.goals.associate(context, goal.id, target, kind)
        api.goals.associate(context, goal.id, target, kind)
        assert api.goals.associated_ids(context, goal.id)[kind + "_ids"] == [target]
        api.goals.remove(context, goal.id, target, kind)
        assert api.goals.associated_ids(context, goal.id)[kind + "_ids"] == []
    finally:
        connection.close()


@pytest.mark.parametrize(
    "frequency,config",
    [
        pytest.param(HabitFrequencyType.DAILY, {}, id="daily"),
        pytest.param(HabitFrequencyType.WEEKDAYS, {"days": ["monday"]}, id="monday"),
        pytest.param(HabitFrequencyType.WEEKDAYS, {"days": ["friday"]}, id="friday"),
        pytest.param(HabitFrequencyType.WEEKDAYS, {"days": ["monday", "wednesday", "friday"]}, id="weekday-set"),
        pytest.param(HabitFrequencyType.SELECTED_DAYS, {"days": [0]}, id="selected-monday"),
        pytest.param(HabitFrequencyType.SELECTED_DAYS, {"days": [6]}, id="selected-sunday"),
        pytest.param(HabitFrequencyType.SELECTED_DAYS, {"days": [0, 2, 4]}, id="selected-set"),
        pytest.param(HabitFrequencyType.TIMES_PER_WEEK, {"count": 1}, id="times-one"),
        pytest.param(HabitFrequencyType.TIMES_PER_WEEK, {"count": 4}, id="times-four"),
        pytest.param(HabitFrequencyType.TIMES_PER_WEEK, {"count": 7}, id="times-seven"),
    ],
)
def test_internal_habit_schedule_matrix_accepts_valid_boundaries(tmp_path, frequency, config):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        habit = api.habits.create(context, HabitCreateContract("scheduled", frequency_type=frequency, frequency_config=config))
        assert habit.frequency_type is frequency
        assert habit.frequency_config == config if frequency is HabitFrequencyType.DAILY else habit.frequency_config == config
    finally:
        connection.close()


@pytest.mark.parametrize(
    "frequency,config",
    [
        pytest.param(HabitFrequencyType.WEEKDAYS, {"days": []}, id="empty-weekdays"),
        pytest.param(HabitFrequencyType.WEEKDAYS, {"days": ["saturday"]}, id="weekend-in-weekdays"),
        pytest.param(HabitFrequencyType.SELECTED_DAYS, {"days": []}, id="empty-selected"),
        pytest.param(HabitFrequencyType.SELECTED_DAYS, {"days": [7]}, id="selected-out-of-range"),
        pytest.param(HabitFrequencyType.SELECTED_DAYS, {"days": [-1]}, id="selected-negative"),
        pytest.param(HabitFrequencyType.SELECTED_DAYS, {"days": [True]}, id="selected-boolean"),
        pytest.param(HabitFrequencyType.TIMES_PER_WEEK, {"count": 0}, id="times-zero"),
        pytest.param(HabitFrequencyType.TIMES_PER_WEEK, {"count": 8}, id="times-eight"),
        pytest.param(HabitFrequencyType.TIMES_PER_WEEK, {"count": True}, id="times-boolean"),
    ],
)
def test_internal_habit_schedule_matrix_rejects_invalid_boundaries(tmp_path, frequency, config):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        with pytest.raises(InternalValidationError):
            api.habits.create(context, "invalid", frequency_type=frequency, frequency_config=config)
        assert api.habits.list(context) == []
    finally:
        connection.close()


@pytest.mark.parametrize(
    "status",
    [HabitCheckInStatus.COMPLETED, HabitCheckInStatus.SKIPPED, HabitCheckInStatus.NOT_DONE],
    ids=["completed", "skipped", "not-done"],
)
def test_internal_checkin_status_upsert_and_lookup(tmp_path, status):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        habit = api.habits.create(context, "checkin")
        when = date(2026, 3, 3)
        created = api.habits.check_in(context, habit.id, CheckInCreateContract(when, status, "note"))
        replaced = api.habits.check_in(context, habit.id, when, HabitCheckInStatus.COMPLETED)
        assert created.status is status
        assert replaced.status is HabitCheckInStatus.COMPLETED
        assert api.habits.get_check_in(context, habit.id, when).status is HabitCheckInStatus.COMPLETED
    finally:
        connection.close()


@pytest.mark.parametrize("limit", [0, 1, 2, 30, 100, 1000], ids=["zero", "one", "two", "default", "max", "clamped"])
def test_internal_checkin_history_limits_are_safe(tmp_path, limit):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        habit = api.habits.create(context, "history")
        for offset in range(3):
            api.habits.check_in(context, habit.id, date(2026, 3, 1 + offset))
        history = api.habits.recent_check_ins(context, habit.id, limit)
        assert 1 <= len(history) <= min(max(limit, 1), 100, 3)
        assert [x.date for x in history] == sorted((x.date for x in history), reverse=True)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "ids",
    [
        pytest.param((1, 2, 3), id="identity"),
        pytest.param((3, 2, 1), id="reverse"),
        pytest.param((2, 3, 1), id="rotation"),
        pytest.param((1,), id="single"),
    ],
)
def test_stack_reorder_preserves_exact_membership_and_positions(tmp_path, ids):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        stacks = [api.habit_stacks.create(context, f"stack-{index}") for index in range(len(ids))]
        actual_ids = tuple(stack.id for stack in stacks)
        requested = tuple(actual_ids[index - 1] for index in ids)
        api.habit_stacks.reorder_stacks(context, ReorderContract(requested))
        result = api.habit_stacks.list(context)
        assert {x.id for x in result} == set(actual_ids)
        assert [x.position for x in result] == list(range(len(result)))
        assert [x.id for x in result] == list(requested)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "bad_ids",
    [(1, 1), (1,), (1, 2, 99), ()],
    ids=["duplicate", "partial", "unknown", "empty"],
)
def test_stack_reorder_rejects_non_exact_sets_without_mutation(tmp_path, bad_ids):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        stacks = [api.habit_stacks.create(context, "one"), api.habit_stacks.create(context, "two")]
        before = [(x.id, x.position) for x in api.habit_stacks.list(context)]
        requested = tuple(stacks[index - 1].id if index in (1, 2) else index for index in bad_ids)
        with pytest.raises(InternalValidationError):
            api.habit_stacks.reorder_stacks(context, ReorderContract(requested))
        assert [(x.id, x.position) for x in api.habit_stacks.list(context)] == before
    finally:
        connection.close()


@pytest.mark.parametrize(
    "selected,include_completed",
    [
        pytest.param(date(2026, 4, 1), False, id="selected-open"),
        pytest.param(date(2026, 4, 1), True, id="selected-completed"),
        pytest.param(date(2026, 4, 2), False, id="next-day-open"),
        pytest.param(date(2026, 4, 2), True, id="next-day-completed"),
        pytest.param(date(2026, 4, 5), True, id="weekend-completed"),
        pytest.param(date(2026, 4, 6), True, id="following-week"),
    ],
)
def test_today_contract_matrix_is_date_stable_and_complete(tmp_path, selected, include_completed):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        task = api.tasks.create(context, TaskCreateContract("today", is_today=True, due_date=date(2026, 4, 1)))
        api.tasks.complete(context, task.id)
        habit = api.habits.create(context, HabitCreateContract("daily"))
        result = api.today.get(context, TodayQueryContract(selected, include_completed))
        assert result.date == selected
        assert all(item.id != task.id for item in result.tasks)
        if include_completed:
            assert [item.id for item in result.completed.tasks] == [task.id]
        else:
            assert result.completed.tasks == []
        assert result.unstacked_habits[0].id == habit.id
    finally:
        connection.close()


@pytest.mark.parametrize(
    "operation",
    [
        pytest.param("auth.current_user", id="auth-current-user"),
        pytest.param("users.list", id="users-list"),
        pytest.param("inbox.list", id="inbox-list"),
        pytest.param("goals.list", id="goals-list"),
        pytest.param("projects.list", id="projects-list"),
        pytest.param("tasks.list", id="tasks-list"),
        pytest.param("habits.list", id="habits-list"),
        pytest.param("habit_stacks.list", id="habit-stacks-list"),
        pytest.param("today.get", id="today-get"),
    ],
)
def test_every_namespace_requires_an_internal_context(operation, tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        namespace, method = operation.split(".")
        with pytest.raises(Exception) as error:
            getattr(getattr(api, namespace), method)(None)
        assert error.type.__name__ == "InvalidContextError"
    finally:
        connection.close()
