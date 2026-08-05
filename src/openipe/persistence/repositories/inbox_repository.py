"""Inbox item persistence with explicit user scoping."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from openipe.core.models.inbox import InboxItem, InboxStatus


class InboxRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(self, user_id: int, text: str) -> InboxItem:
        now = _timestamp(datetime.now(UTC))
        cursor = self.connection.execute(
            """
            INSERT INTO inbox_items(user_id, text, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, text, InboxStatus.UNPROCESSED.value, now, now),
        )
        self.connection.commit()
        return self.get(user_id, cursor.lastrowid)

    def get(self, user_id: int, item_id: int) -> InboxItem | None:
        row = self.connection.execute(
            "SELECT * FROM inbox_items WHERE user_id = ? AND id = ?",
            (user_id, item_id),
        ).fetchone()
        return _to_item(row) if row else None

    def list(self, user_id: int, status: InboxStatus | None = None) -> list[InboxItem]:
        if status is None:
            rows = self.connection.execute(
                "SELECT * FROM inbox_items WHERE user_id = ? ORDER BY created_at DESC, id DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT * FROM inbox_items
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC, id DESC
                """,
                (user_id, status.value),
            ).fetchall()
        return [_to_item(row) for row in rows]

    def update(
        self,
        user_id: int,
        item_id: int,
        text: str,
        status: InboxStatus,
        processed_at: datetime | None,
        archived_at: datetime | None,
    ) -> InboxItem | None:
        now = datetime.now(UTC)
        self.connection.execute(
            """
            UPDATE inbox_items
            SET text = ?, status = ?, updated_at = ?, processed_at = ?, archived_at = ?
            WHERE user_id = ? AND id = ?
            """,
            (
                text,
                status.value,
                _timestamp(now),
                _timestamp(processed_at) if processed_at else None,
                _timestamp(archived_at) if archived_at else None,
                user_id,
                item_id,
            ),
        )
        self.connection.commit()
        return self.get(user_id, item_id)


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _to_item(row: sqlite3.Row) -> InboxItem:
    return InboxItem(
        id=row["id"],
        user_id=row["user_id"],
        text=row["text"],
        status=InboxStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        processed_at=_parse_optional(row["processed_at"]),
        archived_at=_parse_optional(row["archived_at"]),
    )


def _parse_optional(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
