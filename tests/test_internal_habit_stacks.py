import pytest

from openipe.api.internal.errors import InternalNotFoundError, InternalValidationError
from tests.internal_support import admin, make_internal


def test_stack_membership_ordering_and_unstacked_query(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        first = api.habits.create(context, "First")
        second = api.habits.create(context, "Second")
        stack = api.habit_stacks.create(context, "Morning")
        api.habit_stacks.add_habit(context, stack.id, first.id)
        api.habit_stacks.add_habit(context, stack.id, second.id)
        api.habit_stacks.reorder_habits(context, stack.id, [second.id, first.id])
        assert [x.id for x in api.habit_stacks.get(context, stack.id).habits] == [second.id, first.id]
        with pytest.raises(InternalValidationError):
            api.habit_stacks.reorder_habits(context, stack.id, [first.id])
        assert api.habit_stacks.unstacked(context) == []
        with pytest.raises(InternalNotFoundError):
            api.habit_stacks.get(context, 9999)
    finally:
        connection.close()
