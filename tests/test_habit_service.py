from datetime import date

import pytest

from openipe.application.auth_service import AuthService
from openipe.application.habit_service import HabitService
from openipe.application.inbox_service import InboxService
from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.habit import HabitCheckInStatus, HabitFrequencyType
from openipe.persistence.database import initialize_database


def services(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    auth = AuthService(connection)
    user = auth.create_initial_admin("admin", "Administrator", "admin-pass")
    return connection, user, HabitService(connection), InboxService(connection)


def test_habit_frequency_validation_and_scheduling(tmp_path):
    connection, user, habits, _ = services(tmp_path)
    try:
        daily = habits.create(user.id, "Meditate")
        assert habits.is_scheduled(user.id, daily, date(2026, 8, 9))
        weekdays = habits.create(user.id, "Work review", frequency_type=HabitFrequencyType.WEEKDAYS,
                                frequency_config={"days": ["monday", "friday"]})
        assert habits.is_scheduled(user.id, weekdays, date(2026, 8, 7))
        assert not habits.is_scheduled(user.id, weekdays, date(2026, 8, 8))
        selected = habits.create(user.id, "Write", frequency_type=HabitFrequencyType.SELECTED_DAYS,
                                 frequency_config={"days": [0, 2]})
        assert habits.is_scheduled(user.id, selected, date(2026, 8, 5))
        assert not habits.is_scheduled(user.id, selected, date(2026, 8, 6))
        weekly = habits.create(user.id, "Exercise", frequency_type=HabitFrequencyType.TIMES_PER_WEEK,
                               frequency_config={"count": 2})
        assert habits.is_scheduled(user.id, weekly, date(2026, 8, 3))
        habits.check_in(user.id, weekly.id, date(2026, 8, 3))
        assert habits.is_scheduled(user.id, weekly, date(2026, 8, 4))
        habits.check_in(user.id, weekly.id, date(2026, 8, 4))
        assert habits.is_scheduled(user.id, weekly, date(2026, 8, 4))
        assert not habits.is_scheduled(user.id, weekly, date(2026, 8, 5))
    finally:
        connection.close()


@pytest.mark.parametrize(
    "frequency_type,config",
    [
        (HabitFrequencyType.WEEKDAYS, {"days": ["someday"]}),
        (HabitFrequencyType.SELECTED_DAYS, {"days": [7]}),
        (HabitFrequencyType.TIMES_PER_WEEK, {"count": 0}),
    ],
)
def test_invalid_frequency_config_is_rejected(tmp_path, frequency_type, config):
    connection, user, habits, _ = services(tmp_path)
    try:
        with pytest.raises(ValidationError):
            habits.create(user.id, "Invalid", frequency_type=frequency_type, frequency_config=config)
    finally:
        connection.close()


def test_habit_update_activation_archive_and_minimum_version(tmp_path):
    connection, user, habits, _ = services(tmp_path)
    try:
        habit = habits.create(user.id, "Project work", minimum_version="Ten minutes")
        inactive = habits.deactivate(user.id, habit.id)
        assert not inactive.active
        active = habits.activate(user.id, habit.id)
        assert active.active
        archived = habits.archive(user.id, habit.id)
        assert not archived.active
        assert archived.archived_at is not None
        with pytest.raises(ValidationError, match="cannot be activated"):
            habits.activate(user.id, habit.id)
    finally:
        connection.close()


def test_checkin_upsert_history_and_delete(tmp_path):
    connection, user, habits, _ = services(tmp_path)
    try:
        habit = habits.create(user.id, "Read")
        checked = habits.check_in(user.id, habit.id, date(2026, 8, 5), note="A little progress")
        assert checked.status == HabitCheckInStatus.COMPLETED
        updated = habits.check_in(user.id, habit.id, date(2026, 8, 5), HabitCheckInStatus.SKIPPED)
        assert updated.id == checked.id
        assert updated.status == HabitCheckInStatus.SKIPPED
        assert habits.recent_check_ins(user.id, habit.id)[0].status == HabitCheckInStatus.SKIPPED
        habits.delete_check_in(user.id, habit.id, date(2026, 8, 5))
        assert habits.get_check_in(user.id, habit.id, date(2026, 8, 5)) is None
        with pytest.raises(NotFoundError):
            habits.delete_check_in(user.id, habit.id, date(2026, 8, 5))
    finally:
        connection.close()


def test_inbox_habit_conversion_preserves_original(tmp_path):
    connection, user, habits, inbox = services(tmp_path)
    try:
        item = inbox.create(user.id, "Exercise")
        habit = habits.create(user.id, item.text, source_inbox_item_id=item.id)
        assert habit.source_inbox_item_id == item.id
        assert inbox.get(user.id, item.id).status.value == "unprocessed"
        with pytest.raises(NotFoundError):
            habits.create(user.id + 1, "Other", source_inbox_item_id=item.id)
    finally:
        connection.close()
