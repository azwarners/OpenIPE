"""Habit stack persistence."""

from __future__ import annotations

from datetime import UTC, datetime
import sqlite3

from openipe.core.models.habit_stack import HabitStack


class HabitStackRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(self, user_id, name, description) -> HabitStack:
        now = _timestamp(datetime.now(UTC))
        position = self.connection.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 FROM habit_stacks WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]
        cursor = self.connection.execute(
            """INSERT INTO habit_stacks(user_id, name, description, position, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, name, description, position, now, now),
        )
        self.connection.commit()
        return self.get(user_id, cursor.lastrowid)

    def get(self, user_id, stack_id) -> HabitStack | None:
        row = self.connection.execute(
            "SELECT * FROM habit_stacks WHERE user_id = ? AND id = ?", (user_id, stack_id)
        ).fetchone()
        return _to_stack(row) if row else None

    def list(self, user_id, active=None) -> list[HabitStack]:
        query = "SELECT * FROM habit_stacks WHERE user_id = ?"
        params: list[object] = [user_id]
        if active is not None:
            query += " AND active = ?"
            params.append(int(active))
        query += " ORDER BY position, id"
        return [_to_stack(row) for row in self.connection.execute(query, params).fetchall()]

    def update(self, user_id, stack_id, name, description, active, archived_at) -> HabitStack | None:
        self.connection.execute(
            """UPDATE habit_stacks SET name = ?, description = ?, active = ?, updated_at = ?, archived_at = ?
            WHERE user_id = ? AND id = ?""",
            (name, description, int(active), _timestamp(datetime.now(UTC)),
             _timestamp(archived_at) if archived_at else None, user_id, stack_id),
        )
        self.connection.commit()
        return self.get(user_id, stack_id)

    def reorder(self, user_id, stack_ids: list[int]) -> None:
        for position, stack_id in enumerate(stack_ids):
            self.connection.execute(
                "UPDATE habit_stacks SET position = ?, updated_at = ? WHERE user_id = ? AND id = ?",
                (position, _timestamp(datetime.now(UTC)), user_id, stack_id),
            )
        self.connection.commit()


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _to_stack(row: sqlite3.Row) -> HabitStack:
    return HabitStack(row["id"], row["user_id"], row["name"], row["description"], row["position"],
                      bool(row["active"]), datetime.fromisoformat(row["created_at"]),
                      datetime.fromisoformat(row["updated_at"]), _parse(row["archived_at"]))


def _parse(value):
    return datetime.fromisoformat(value) if value else None
