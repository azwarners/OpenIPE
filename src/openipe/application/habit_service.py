"""Habit scheduling and check-in application service."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import sqlite3

from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.habit import Habit, HabitCheckIn, HabitCheckInStatus, HabitFrequencyType
from openipe.persistence.repositories.habit_repository import HabitCheckInRepository, HabitRepository
from openipe.persistence.repositories.inbox_repository import InboxRepository

UNSET = object()
WEEKDAY_NAMES = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}


class HabitService:
    def __init__(self, connection: sqlite3.Connection):
        self.repository = HabitRepository(connection)
        self.checkins = HabitCheckInRepository(connection)
        self.inbox = InboxRepository(connection)

    def create(self, user_id, title, description=None, frequency_type=HabitFrequencyType.DAILY,
               frequency_config=None, minimum_version=None, source_inbox_item_id=None) -> Habit:
        if source_inbox_item_id is not None and self.inbox.get(user_id, source_inbox_item_id) is None:
            raise NotFoundError("Source inbox item not found")
        normalized_type = _frequency_type(frequency_type)
        config = _validate_schedule(normalized_type, frequency_config or {})
        return self.repository.create(user_id, _title(title), _description(description), normalized_type,
                                      config, _optional_text(minimum_version), source_inbox_item_id)

    def list(self, user_id, active=None) -> list[Habit]:
        return self.repository.list(user_id, active)

    def get(self, user_id, habit_id) -> Habit:
        habit = self.repository.get(user_id, habit_id)
        if habit is None:
            raise NotFoundError("Habit not found")
        return habit

    def update(self, user_id, habit_id, title=UNSET, description=UNSET, frequency_type=UNSET,
               frequency_config=UNSET, minimum_version=UNSET, active=UNSET,
               source_inbox_item_id=UNSET) -> Habit:
        habit = self.get(user_id, habit_id)
        if source_inbox_item_id is not UNSET and source_inbox_item_id is not None and \
                self.inbox.get(user_id, source_inbox_item_id) is None:
            raise NotFoundError("Source inbox item not found")
        if habit.archived_at is not None and active is not UNSET and active:
            raise ValidationError("Archived habits cannot be activated")
        normalized_type = _frequency_type(frequency_type if frequency_type is not UNSET else habit.frequency_type)
        config = _validate_schedule(
            normalized_type,
            frequency_config if frequency_config is not UNSET else habit.frequency_config,
        )
        return self.repository.update(
            user_id, habit_id,
            _title(title) if title is not UNSET and title is not None else habit.title,
            _description(description) if description is not UNSET else habit.description,
            normalized_type, config,
            _optional_text(minimum_version) if minimum_version is not UNSET else habit.minimum_version,
            bool(active) if active is not UNSET else habit.active,
            source_inbox_item_id if source_inbox_item_id is not UNSET else habit.source_inbox_item_id,
            habit.archived_at,
        )

    def activate(self, user_id, habit_id):
        return self.update(user_id, habit_id, active=True)

    def deactivate(self, user_id, habit_id):
        return self.update(user_id, habit_id, active=False)

    def archive(self, user_id, habit_id) -> Habit:
        habit = self.get(user_id, habit_id)
        if habit.archived_at is not None:
            return habit
        return self.repository.update(user_id, habit_id, habit.title, habit.description, habit.frequency_type,
                                      habit.frequency_config, habit.minimum_version, False,
                                      habit.source_inbox_item_id, datetime.now(UTC))

    def check_in(self, user_id, habit_id, checkin_date, checkin_status=HabitCheckInStatus.COMPLETED, note=None) -> HabitCheckIn:
        habit = self.get(user_id, habit_id)
        if habit.archived_at is not None:
            raise ValidationError("Archived habits cannot be checked in")
        try:
            normalized_status = checkin_status if isinstance(checkin_status, HabitCheckInStatus) else HabitCheckInStatus(checkin_status)
        except ValueError as error:
            raise ValidationError("Invalid habit check-in status") from error
        return self.checkins.upsert(user_id, habit.id, checkin_date, normalized_status, _description(note))

    def get_check_in(self, user_id, habit_id, checkin_date) -> HabitCheckIn | None:
        self.get(user_id, habit_id)
        return self.checkins.get(user_id, habit_id, checkin_date)

    def recent_check_ins(self, user_id, habit_id, limit=30) -> list[HabitCheckIn]:
        self.get(user_id, habit_id)
        return self.checkins.list(user_id, habit_id, max(1, min(limit, 100)))

    def delete_check_in(self, user_id, habit_id, checkin_date) -> None:
        self.get(user_id, habit_id)
        if not self.checkins.delete(user_id, habit_id, checkin_date):
            raise NotFoundError("Habit check-in not found")

    def is_scheduled(self, user_id, habit: Habit, selected_date: date) -> bool:
        if not habit.active or habit.archived_at is not None:
            return False
        config = habit.frequency_config
        if habit.frequency_type == HabitFrequencyType.DAILY:
            return True
        if habit.frequency_type == HabitFrequencyType.WEEKDAYS:
            return selected_date.weekday() < 5 and _weekday_name(selected_date) in config["days"]
        if habit.frequency_type == HabitFrequencyType.SELECTED_DAYS:
            return selected_date.weekday() in config["days"]
        start = selected_date - timedelta(days=selected_date.weekday())
        current = self.checkins.get(user_id, habit.id, selected_date)
        completed_before = self.checkins.completed_count_between(user_id, habit.id, start, selected_date - timedelta(days=1))
        return current is not None or completed_before < config["count"]


def _frequency_type(value):
    try:
        return value if isinstance(value, HabitFrequencyType) else HabitFrequencyType(value)
    except ValueError as error:
        raise ValidationError("Invalid habit frequency type") from error


def _validate_schedule(frequency_type, config):
    if not isinstance(config, dict):
        raise ValidationError("Frequency config must be an object")
    if frequency_type == HabitFrequencyType.DAILY:
        return {}
    days = config.get("days")
    if frequency_type == HabitFrequencyType.WEEKDAYS:
        if not isinstance(days, list) or not days or any(day not in {"monday", "tuesday", "wednesday", "thursday", "friday"} for day in days):
            raise ValidationError("Weekday schedule requires weekday names")
        return {"days": sorted(set(days), key=("monday", "tuesday", "wednesday", "thursday", "friday").index)}
    if frequency_type == HabitFrequencyType.SELECTED_DAYS:
        if not isinstance(days, list) or not days or any(not isinstance(day, int) or isinstance(day, bool) or day not in range(7) for day in days):
            raise ValidationError("Selected-days schedule requires day numbers from 0 through 6")
        return {"days": sorted(set(days))}
    count = config.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count not in range(1, 8):
        raise ValidationError("Times-per-week schedule requires a count from 1 through 7")
    return {"count": count}


def _weekday_name(value):
    return ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")[value.weekday()]


def _title(value):
    value = value.strip()
    if not value:
        raise ValidationError("Habit title must not be empty")
    return value


def _description(value):
    if value is None:
        return None
    value = value.strip()
    return value or None


def _optional_text(value):
    return _description(value)
