import pytest
from datetime import date

from openipe.api.internal.errors import InternalNotFoundError, InternalValidationError
from openipe.core.models.habit import HabitFrequencyType
from tests.internal_support import admin, make_internal


def test_habit_schedule_and_checkins(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        habit = api.habits.create(context, "Daily", frequency_type=HabitFrequencyType.DAILY)
        checkin = api.habits.check_in(context, habit.id, date(2026, 1, 1))
        assert checkin.habit_id == habit.id
        assert len(api.habits.recent_check_ins(context, habit.id)) == 1
        api.habits.delete_check_in(context, habit.id, date(2026, 1, 1))
        with pytest.raises(InternalValidationError):
            api.habits.create(context, "Bad", frequency_type=HabitFrequencyType.SELECTED_DAYS, frequency_config={"days": []})
        with pytest.raises(InternalNotFoundError):
            api.habits.get(context, 9999)
    finally:
        connection.close()
