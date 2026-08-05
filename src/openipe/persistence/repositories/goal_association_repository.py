"""Many-to-many Goal association persistence."""

from __future__ import annotations

import sqlite3


class GoalAssociationRepository:
    _TABLES = {
        "project": ("goal_projects", "project_id"),
        "task": ("goal_tasks", "task_id"),
        "habit": ("goal_habits", "habit_id"),
    }

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def ids(self, kind: str, goal_id: int) -> list[int]:
        table, column = self._table(kind)
        rows = self.connection.execute(
            f"SELECT {column} FROM {table} WHERE goal_id = ? ORDER BY {column}", (goal_id,)
        ).fetchall()
        return [row[0] for row in rows]

    def add(self, kind: str, goal_id: int, related_id: int) -> None:
        table, column = self._table(kind)
        self.connection.execute(
            f"INSERT OR IGNORE INTO {table}(goal_id, {column}) VALUES (?, ?)",
            (goal_id, related_id),
        )
        self.connection.commit()

    def remove(self, kind: str, goal_id: int, related_id: int) -> None:
        table, column = self._table(kind)
        self.connection.execute(
            f"DELETE FROM {table} WHERE goal_id = ? AND {column} = ?",
            (goal_id, related_id),
        )
        self.connection.commit()

    def goal_ids_for_related(self, kind: str, related_id: int) -> list[int]:
        table, column = self._table(kind)
        rows = self.connection.execute(
            f"SELECT goal_id FROM {table} WHERE {column} = ? ORDER BY goal_id", (related_id,)
        ).fetchall()
        return [row[0] for row in rows]

    @classmethod
    def _table(cls, kind: str) -> tuple[str, str]:
        try:
            return cls._TABLES[kind]
        except KeyError as error:
            raise ValueError(f"Unknown goal association kind: {kind}") from error
