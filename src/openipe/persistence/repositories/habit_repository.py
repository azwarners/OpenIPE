"""Habit and check-in persistence."""

from __future__ import annotations

from datetime import UTC, date, datetime
import json
import sqlite3

from openipe.core.models.habit import Habit, HabitCheckIn, HabitCheckInStatus, HabitFrequencyType


class HabitRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(self, user_id, title, description, frequency_type, frequency_config,
               minimum_version, source_inbox_item_id) -> Habit:
        now = _timestamp(datetime.now(UTC))
        cursor = self.connection.execute(
            """INSERT INTO habits(user_id, title, description, frequency_type, frequency_config,
            minimum_version, source_inbox_item_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, title, description, frequency_type.value, json.dumps(frequency_config, sort_keys=True),
             minimum_version, source_inbox_item_id, now, now),
        )
        self.connection.commit()
        return self.get(user_id, cursor.lastrowid)

    def get(self, user_id, habit_id) -> Habit | None:
        row = self.connection.execute("SELECT * FROM habits WHERE user_id = ? AND id = ?", (user_id, habit_id)).fetchone()
        return _to_habit(row) if row else None

    def list(self, user_id, active=None) -> list[Habit]:
        query = "SELECT * FROM habits WHERE user_id = ?"
        params: list[object] = [user_id]
        if active is not None:
            query += " AND active = ?"
            params.append(int(active))
        query += " ORDER BY position, created_at DESC, id DESC"
        return [_to_habit(row) for row in self.connection.execute(query, params).fetchall()]

    def update(self, user_id, habit_id, title, description, frequency_type, frequency_config,
               minimum_version, active, source_inbox_item_id, archived_at) -> Habit | None:
        self.connection.execute(
            """UPDATE habits SET title = ?, description = ?, frequency_type = ?, frequency_config = ?,
            minimum_version = ?, active = ?, source_inbox_item_id = ?, updated_at = ?, archived_at = ?
            WHERE user_id = ? AND id = ?""",
            (title, description, frequency_type.value, json.dumps(frequency_config, sort_keys=True), minimum_version,
             int(active), source_inbox_item_id, _timestamp(datetime.now(UTC)),
             _timestamp(archived_at) if archived_at else None, user_id, habit_id),
        )
        self.connection.commit()
        return self.get(user_id, habit_id)

    def set_stack(self, user_id, habit_id, stack_id, position) -> Habit | None:
        self.connection.execute(
            "UPDATE habits SET stack_id = ?, position = ?, updated_at = ? WHERE user_id = ? AND id = ?",
            (stack_id, position, _timestamp(datetime.now(UTC)), user_id, habit_id),
        )
        self.connection.commit()
        return self.get(user_id, habit_id)

    def list_by_stack(self, user_id, stack_id) -> list[Habit]:
        rows = self.connection.execute(
            "SELECT * FROM habits WHERE user_id = ? AND stack_id = ? ORDER BY position, id",
            (user_id, stack_id),
        ).fetchall()
        return [_to_habit(row) for row in rows]

    def max_position_in_stack(self, user_id, stack_id) -> int:
        value = self.connection.execute(
            "SELECT MAX(position) FROM habits WHERE user_id = ? AND stack_id = ?",
            (user_id, stack_id),
        ).fetchone()[0]
        return value if value is not None else -1

    def reorder_in_stack(self, user_id, stack_id, habit_ids: list[int]) -> None:
        for position, habit_id in enumerate(habit_ids):
            self.connection.execute(
                "UPDATE habits SET position = ?, updated_at = ? WHERE user_id = ? AND stack_id = ? AND id = ?",
                (position, _timestamp(datetime.now(UTC)), user_id, stack_id, habit_id),
            )
        self.connection.commit()


class HabitCheckInRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def upsert(self, user_id, habit_id, checkin_date, checkin_status, note) -> HabitCheckIn:
        now = _timestamp(datetime.now(UTC))
        self.connection.execute(
            """INSERT INTO habit_checkins(user_id, habit_id, date, status, note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(habit_id, date) DO UPDATE SET status = excluded.status, note = excluded.note,
            updated_at = excluded.updated_at""",
            (user_id, habit_id, checkin_date.isoformat(), checkin_status.value, note, now, now),
        )
        self.connection.commit()
        return self.get(user_id, habit_id, checkin_date)

    def get(self, user_id, habit_id, checkin_date) -> HabitCheckIn | None:
        row = self.connection.execute(
            "SELECT * FROM habit_checkins WHERE user_id = ? AND habit_id = ? AND date = ?",
            (user_id, habit_id, checkin_date.isoformat()),
        ).fetchone()
        return _to_checkin(row) if row else None

    def list(self, user_id, habit_id, limit=30) -> list[HabitCheckIn]:
        rows = self.connection.execute(
            "SELECT * FROM habit_checkins WHERE user_id = ? AND habit_id = ? ORDER BY date DESC LIMIT ?",
            (user_id, habit_id, limit),
        ).fetchall()
        return [_to_checkin(row) for row in rows]

    def delete(self, user_id, habit_id, checkin_date) -> bool:
        cursor = self.connection.execute(
            "DELETE FROM habit_checkins WHERE user_id = ? AND habit_id = ? AND date = ?",
            (user_id, habit_id, checkin_date.isoformat()),
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def completed_count_between(self, user_id, habit_id, start, end) -> int:
        return self.connection.execute(
            """SELECT COUNT(*) FROM habit_checkins WHERE user_id = ? AND habit_id = ?
            AND date >= ? AND date <= ? AND status = 'completed'""",
            (user_id, habit_id, start.isoformat(), end.isoformat()),
        ).fetchone()[0]


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _to_habit(row: sqlite3.Row) -> Habit:
    return Habit(row["id"], row["user_id"], row["title"], row["description"],
                 HabitFrequencyType(row["frequency_type"]), json.loads(row["frequency_config"]),
                 row["minimum_version"], row["stack_id"], row["position"], bool(row["active"]),
                 row["source_inbox_item_id"], datetime.fromisoformat(row["created_at"]),
                 datetime.fromisoformat(row["updated_at"]), _parse(row["archived_at"]))


def _to_checkin(row: sqlite3.Row) -> HabitCheckIn:
    return HabitCheckIn(row["id"], row["user_id"], row["habit_id"], date.fromisoformat(row["date"]),
                        HabitCheckInStatus(row["status"]), row["note"], datetime.fromisoformat(row["created_at"]),
                        datetime.fromisoformat(row["updated_at"]))


def _parse(value):
    return datetime.fromisoformat(value) if value else None
