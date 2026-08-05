from datetime import date

import pytest

from openipe.application.auth_service import AuthService
from openipe.application.habit_service import HabitService
from openipe.application.habit_stack_service import HabitStackService
from openipe.core.errors import ValidationError
from openipe.core.models.habit import HabitCheckInStatus
from openipe.persistence.database import initialize_database


def services(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    auth = AuthService(connection)
    user = auth.create_initial_admin("admin", "Administrator", "admin-pass")
    return connection, user, HabitStackService(connection), HabitService(connection)


def test_stack_membership_order_and_unstacked_habits(tmp_path):
    connection, user, stacks, habits = services(tmp_path)
    try:
        first_stack = stacks.create(user.id, "Morning Routine")
        second_stack = stacks.create(user.id, "Evening Routine")
        first = habits.create(user.id, "Meditate")
        second = habits.create(user.id, "Read")
        unstacked = habits.create(user.id, "Plan tomorrow")
        stacks.add_habit(user.id, first_stack.id, first.id)
        stacks.add_habit(user.id, first_stack.id, second.id)
        assert [item.id for item in stacks.habits_in_stack(user.id, first_stack.id)] == [first.id, second.id]
        stacks.reorder_habits(user.id, first_stack.id, [second.id, first.id])
        assert [item.id for item in stacks.habits_in_stack(user.id, first_stack.id)] == [second.id, first.id]
        stacks.remove_habit(user.id, first_stack.id, second.id)
        assert [item.id for item in stacks.habits_in_stack(user.id, first_stack.id)] == [first.id]
        assert [item.id for item in stacks.unstacked_habits(user.id)] == [unstacked.id, second.id]
        stacks.add_habit(user.id, second_stack.id, second.id)
        assert habits.get(user.id, second.id).stack_id == second_stack.id
    finally:
        connection.close()


def test_stack_and_habit_order_validation(tmp_path):
    connection, user, stacks, habits = services(tmp_path)
    try:
        first = stacks.create(user.id, "First")
        second = stacks.create(user.id, "Second")
        with pytest.raises(ValidationError, match="exactly once"):
            stacks.reorder_stacks(user.id, [first.id, first.id])
        stacks.reorder_stacks(user.id, [second.id, first.id])
        assert [stack.id for stack in stacks.list(user.id, active=True)] == [second.id, first.id]
        habit = habits.create(user.id, "One")
        stacks.add_habit(user.id, first.id, habit.id)
        with pytest.raises(ValidationError, match="exactly once"):
            stacks.reorder_habits(user.id, first.id, [])
    finally:
        connection.close()


def test_stack_progress_counts_scheduled_habits_for_date(tmp_path):
    connection, user, stacks, habits = services(tmp_path)
    try:
        stack = stacks.create(user.id, "Morning")
        first = habits.create(user.id, "First")
        second = habits.create(user.id, "Second")
        stacks.add_habit(user.id, stack.id, first.id)
        stacks.add_habit(user.id, stack.id, second.id)
        selected = date(2026, 8, 5)
        assert stacks.progress(user.id, stack.id, selected) == (0, 2)
        habits.check_in(user.id, first.id, selected, HabitCheckInStatus.COMPLETED)
        assert stacks.progress(user.id, stack.id, selected) == (1, 2)
        habits.deactivate(user.id, second.id)
        assert stacks.progress(user.id, stack.id, selected) == (1, 1)
    finally:
        connection.close()


def test_archived_stack_cannot_receive_habits(tmp_path):
    connection, user, stacks, habits = services(tmp_path)
    try:
        stack = stacks.create(user.id, "Archive")
        habit = habits.create(user.id, "Habit")
        archived = stacks.archive(user.id, stack.id)
        assert not archived.active
        with pytest.raises(ValidationError, match="Inactive"):
            stacks.add_habit(user.id, stack.id, habit.id)
    finally:
        connection.close()
