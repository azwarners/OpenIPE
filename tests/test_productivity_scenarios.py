"""End-to-end productivity workflows through the real internal façade."""

from datetime import date

import pytest

from openipe.api.internal import InternalAPI
from openipe.api.internal.errors import InternalAPIError, InternalNotFoundError, InternalValidationError
from openipe.core.config import Settings
from openipe.core.models.habit import HabitCheckInStatus, HabitFrequencyType
from openipe.persistence.database import initialize_database
from tests.internal_support import admin, make_internal


def test_capture_to_completed_project_preserves_links_and_progress(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        inbox = api.inbox.create(context, "  Ship the release 🚀  ")
        project = api.inbox.create_project(context, inbox.id, "release project")
        assert project.source_inbox_item_id == inbox.id
        assert api.inbox.get(context, inbox.id).text == "Ship the release 🚀"
        first = api.tasks.create(context, "Write notes", project_id=project.id, is_today=True)
        second = api.tasks.create(context, "Publish", project_id=project.id, due_date=date(2026, 1, 5))
        assert api.projects.progress(context, project.id) == ([first.id, second.id], 2, 0, 2)
        api.projects.set_next_action(context, project.id, first.id)
        with pytest.raises(InternalValidationError):
            api.projects.set_next_action(context, project.id, second.id + 999)
        api.tasks.complete(context, first.id)
        assert api.projects.get(context, project.id).next_action_task_id is None
        assert api.projects.progress(context, project.id) == ([first.id, second.id], 2, 1, 1)
        api.tasks.complete(context, second.id)
        final = api.projects.complete(context, project.id)
        assert final.status.value == "completed"
        assert final.completed_at is not None
        assert final.next_action_task_id is None
        with pytest.raises(InternalValidationError):
            api.projects.resume(context, project.id)
    finally:
        connection.close()


def test_goal_backed_work_updates_evidence_and_today_context(tmp_path):
    api, connection = make_internal(tmp_path)
    selected = date(2026, 1, 7)
    try:
        _, context = admin(api)
        goal = api.goals.create(context, "Improve health")
        task = api.tasks.create(context, "Walk", is_today=True)
        habit = api.habits.create(context, "Drink water")
        api.goals.associate(context, goal.id, task.id, "task")
        api.goals.associate(context, goal.id, habit.id, "habit")
        before = api.goals.evidence(context, goal.id, selected)
        assert before == {
            "projects_total": 0, "projects_completed": 0, "tasks_total": 1,
            "tasks_completed": 0, "tasks_open": 1, "habits_scheduled": 3,
            "habits_completed": 0,
        }
        today = api.today.get(context, selected)
        assert today.tasks[0].goals[0].id == goal.id
        api.tasks.complete(context, task.id)
        api.habits.check_in(context, habit.id, selected, HabitCheckInStatus.COMPLETED)
        after = api.goals.evidence(context, goal.id, selected)
        assert after["tasks_completed"] == 1
        assert after["tasks_open"] == 0
        assert after["habits_completed"] == 1
        completed = api.today.get(context, selected, include_completed=True)
        assert [item.id for item in completed.completed.tasks] == [task.id]
    finally:
        connection.close()


def test_daily_execution_loop_tracks_stacks_unstacked_habits_and_overdue_tasks(tmp_path):
    api, connection = make_internal(tmp_path)
    selected = date(2026, 1, 10)
    try:
        _, context = admin(api)
        overdue = api.tasks.create(context, "Overdue", is_today=True, due_date=date(2026, 1, 9))
        future = api.tasks.create(context, "Future", is_today=True, due_date=date(2026, 1, 11))
        stack = api.habit_stacks.create(context, "Morning")
        stacked = api.habits.create(context, "Stretch", frequency_type=HabitFrequencyType.DAILY)
        unstacked = api.habits.create(context, "Reflect", frequency_type=HabitFrequencyType.SELECTED_DAYS,
                                      frequency_config={"days": [5]})
        api.habit_stacks.add_habit(context, stack.id, stacked.id)
        before = api.today.get(context, selected)
        assert {item.id for item in before.tasks} == {overdue.id, future.id}
        assert next(item for item in before.tasks if item.id == overdue.id).overdue is True
        assert before.habit_stacks[0].scheduled_count == 1
        assert [item.id for item in before.unstacked_habits] == [unstacked.id]
        api.tasks.complete(context, overdue.id)
        api.habits.check_in(context, stacked.id, selected)
        after = api.today.get(context, selected, include_completed=True)
        assert [item.id for item in after.tasks] == [future.id]
        assert after.habit_stacks[0].completed_count == 1
        assert [item.id for item in after.completed.tasks] == [overdue.id]
        assert [item.id for item in after.completed.habits] == [stacked.id]
    finally:
        connection.close()


def test_habit_establishment_workflow_survives_membership_mutations(tmp_path):
    api, connection = make_internal(tmp_path)
    selected = date(2026, 1, 6)
    try:
        _, context = admin(api)
        inbox = api.inbox.create(context, "Build a routine")
        habit = api.inbox.create_habit(context, inbox.id, frequency_type=HabitFrequencyType.WEEKDAYS,
                                       frequency_config={"days": ["tuesday"]})
        stack = api.habit_stacks.create(context, "Routine")
        goal = api.goals.create(context, "Consistency")
        api.habit_stacks.add_habit(context, stack.id, habit.id)
        api.goals.associate(context, goal.id, habit.id, "habit")
        api.habits.check_in(context, habit.id, selected, HabitCheckInStatus.SKIPPED, "not today")
        assert api.habits.get_check_in(context, habit.id, selected).status == HabitCheckInStatus.SKIPPED
        assert api.habit_stacks.progress(context, stack.id, selected) == (0, 1)
        api.habits.check_in(context, habit.id, selected, HabitCheckInStatus.COMPLETED)
        assert api.habit_stacks.progress(context, stack.id, selected) == (1, 1)
        api.habit_stacks.remove_habit(context, stack.id, habit.id)
        assert [item.id for item in api.habit_stacks.unstacked(context)] == [habit.id]
        assert api.goals.evidence(context, goal.id, selected)["habits_completed"] == 1
    finally:
        connection.close()


def test_multi_user_isolation_covers_conversion_association_and_reordering(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, first = admin(api)
        api.users.create(first, "second", "Second", "second-pass")
        second = api.authenticate(api.auth.login("second", "second-pass").access_token)
        first_item = api.inbox.create(first, "First private idea")
        first_goal = api.goals.create(first, "First goal")
        first_stack = api.habit_stacks.create(first, "First stack")
        first_habit = api.habits.create(first, "First habit")
        for operation in (
            lambda: api.inbox.get(second, first_item.id),
            lambda: api.inbox.create_task(second, first_item.id),
            lambda: api.goals.associate(second, first_goal.id, first_habit.id, "habit"),
            lambda: api.habit_stacks.add_habit(second, first_stack.id, first_habit.id),
            lambda: api.habit_stacks.reorder_stacks(second, [first_stack.id]),
        ):
            with pytest.raises((InternalNotFoundError, InternalValidationError)):
                operation()
        assert api.inbox.list(second) == []
        assert api.habit_stacks.list(second) == []
    finally:
        connection.close()


def test_file_backed_restart_preserves_relationships_ordering_and_checkins(tmp_path):
    path = tmp_path / "restart.sqlite3"
    connection = initialize_database(path)
    api = InternalAPI(connection, Settings(database_path=path))
    _, context = admin(api)
    item = api.inbox.create(context, "Persisted idea")
    project = api.inbox.create_project(context, item.id)
    task = api.tasks.create(context, "Persisted task", project_id=project.id)
    habit = api.habits.create(context, "Persisted habit")
    stack = api.habit_stacks.create(context, "Persisted stack")
    api.habit_stacks.add_habit(context, stack.id, habit.id)
    api.habits.check_in(context, habit.id, date(2026, 2, 1))
    goal = api.goals.create(context, "Persisted goal")
    api.goals.associate(context, goal.id, project.id, "project")
    api.goals.associate(context, goal.id, task.id, "task")
    connection.close()

    reopened = initialize_database(path)
    reopened_api = InternalAPI(reopened, Settings(database_path=path))
    try:
        reopened_context = reopened_api.authenticate(
            reopened_api.auth.login("admin", "admin-pass").access_token
        )
        assert reopened_api.inbox.get(reopened_context, item.id).text == "Persisted idea"
        assert reopened_api.projects.get(reopened_context, project.id).task_ids == [task.id]
        assert reopened_api.habits.recent_check_ins(reopened_context, habit.id)[0].date == date(2026, 2, 1)
        restored_goal = reopened_api.goals.get(reopened_context, goal.id)
        assert restored_goal.project_ids == [project.id]
        assert restored_goal.task_ids == [task.id]
        assert reopened_api.habit_stacks.get(reopened_context, stack.id).habits[0].id == habit.id
    finally:
        reopened.close()
