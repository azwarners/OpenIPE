import pytest
from openipe.api.internal.errors import InternalNotFoundError, InternalValidationError
from openipe.core.models.habit import HabitFrequencyType
from tests.internal_support import admin, make_internal


def test_inbox_and_all_conversion_paths(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        item = api.inbox.create(context, "Captured idea")
        assert api.inbox.create_task(context, item.id).title == "Captured idea"
        item2 = api.inbox.create(context, "Project idea")
        assert api.inbox.create_project(context, item2.id).title == "Project idea"
        item3 = api.inbox.create(context, "Habit idea")
        habit = api.inbox.create_habit(context, item3.id, frequency_type=HabitFrequencyType.DAILY)
        assert habit.title == "Habit idea"
        assert api.inbox.archive(context, item.id).status.value == "archived"
        with pytest.raises(InternalValidationError):
            api.inbox.create(context, "   ")
        with pytest.raises(InternalNotFoundError):
            api.inbox.get(context, 9999)
    finally:
        connection.close()
