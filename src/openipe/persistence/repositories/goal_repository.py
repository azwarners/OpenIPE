"""Goal persistence with explicit user scoping."""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime

from openipe.core.models.goal import Goal, GoalStatus


class GoalRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(
        self,
        user_id: int,
        title: str,
        description: str | None,
        target_date: date | None,
        source_inbox_item_id: int | None,
    ) -> Goal:
        now = _timestamp(datetime.now(UTC))
        cursor = self.connection.execute(
            """
            INSERT INTO goals(
                user_id, title, description, status, target_date,
                created_at, updated_at, source_inbox_item_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                title,
                description,
                GoalStatus.ACTIVE.value,
                target_date.isoformat() if target_date else None,
                now,
                now,
                source_inbox_item_id,
            ),
        )
        self.connection.commit()
        return self.get(user_id, cursor.lastrowid)

    def get(self, user_id: int, goal_id: int) -> Goal | None:
        row = self.connection.execute(
            "SELECT * FROM goals WHERE user_id = ? AND id = ?",
            (user_id, goal_id),
        ).fetchone()
        return _to_goal(row) if row else None

    def list(self, user_id: int, status: GoalStatus | None = None) -> list[Goal]:
        if status is None:
            rows = self.connection.execute(
                "SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC, id DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT * FROM goals WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC, id DESC
                """,
                (user_id, status.value),
            ).fetchall()
        return [_to_goal(row) for row in rows]

    def update(
        self,
        user_id: int,
        goal_id: int,
        title: str,
        description: str | None,
        status: GoalStatus,
        target_date: date | None,
        achieved_at: datetime | None,
        archived_at: datetime | None,
        source_inbox_item_id: int | None,
    ) -> Goal | None:
        self.connection.execute(
            """
            UPDATE goals SET
                title = ?, description = ?, status = ?, target_date = ?, updated_at = ?,
                achieved_at = ?, archived_at = ?, source_inbox_item_id = ?
            WHERE user_id = ? AND id = ?
            """,
            (
                title,
                description,
                status.value,
                target_date.isoformat() if target_date else None,
                _timestamp(datetime.now(UTC)),
                _timestamp(achieved_at) if achieved_at else None,
                _timestamp(archived_at) if archived_at else None,
                source_inbox_item_id,
                user_id,
                goal_id,
            ),
        )
        self.connection.commit()
        return self.get(user_id, goal_id)


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _to_goal(row: sqlite3.Row) -> Goal:
    return Goal(
        id=row["id"],
        user_id=row["user_id"],
        title=row["title"],
        description=row["description"],
        status=GoalStatus(row["status"]),
        target_date=date.fromisoformat(row["target_date"]) if row["target_date"] else None,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        achieved_at=_parse_datetime(row["achieved_at"]),
        archived_at=_parse_datetime(row["archived_at"]),
        source_inbox_item_id=row["source_inbox_item_id"],
    )


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
