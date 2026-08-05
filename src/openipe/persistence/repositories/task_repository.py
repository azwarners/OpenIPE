"""Task persistence with user-scoped queries."""

from __future__ import annotations

from datetime import UTC, date, datetime
import sqlite3

from openipe.core.models.task import Task, TaskPriority, TaskStatus


class TaskRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(self, user_id, title, description, project_id, priority, due_date, is_today, source_inbox_item_id) -> Task:
        now = _timestamp(datetime.now(UTC))
        cursor = self.connection.execute(
            """INSERT INTO tasks(user_id, title, description, project_id, status, priority, due_date, is_today,
            source_inbox_item_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, title, description, project_id, TaskStatus.OPEN.value, priority.value,
             due_date.isoformat() if due_date else None, int(is_today), source_inbox_item_id, now, now),
        )
        self.connection.commit()
        return self.get(user_id, cursor.lastrowid)

    def get(self, user_id, task_id) -> Task | None:
        row = self.connection.execute("SELECT * FROM tasks WHERE user_id = ? AND id = ?", (user_id, task_id)).fetchone()
        return _to_task(row) if row else None

    def list(self, user_id, status=None, project_id=None) -> list[Task]:
        query = "SELECT * FROM tasks WHERE user_id = ?"
        params: list[object] = [user_id]
        if status is not None:
            query += " AND status = ?"; params.append(status.value)
        if project_id is not None:
            query += " AND project_id = ?"; params.append(project_id)
        query += " ORDER BY created_at DESC, id DESC"
        return [_to_task(row) for row in self.connection.execute(query, params).fetchall()]

    def update(self, user_id, task_id, title, description, project_id, status, priority, due_date,
               is_today, source_inbox_item_id, completed_at, archived_at) -> Task | None:
        self.connection.execute(
            """UPDATE tasks SET title = ?, description = ?, project_id = ?, status = ?, priority = ?,
            due_date = ?, is_today = ?, source_inbox_item_id = ?, updated_at = ?, completed_at = ?, archived_at = ?
            WHERE user_id = ? AND id = ?""",
            (title, description, project_id, status.value, priority.value, due_date.isoformat() if due_date else None,
             int(is_today), source_inbox_item_id, _timestamp(datetime.now(UTC)),
             _timestamp(completed_at) if completed_at else None, _timestamp(archived_at) if archived_at else None,
             user_id, task_id),
        )
        self.connection.commit()
        return self.get(user_id, task_id)


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _to_task(row: sqlite3.Row) -> Task:
    return Task(row["id"], row["user_id"], row["title"], row["description"], row["project_id"],
                TaskStatus(row["status"]), TaskPriority(row["priority"]),
                date.fromisoformat(row["due_date"]) if row["due_date"] else None, bool(row["is_today"]),
                row["source_inbox_item_id"], datetime.fromisoformat(row["created_at"]),
                datetime.fromisoformat(row["updated_at"]), _parse(row["completed_at"]), _parse(row["archived_at"]))


def _parse(value):
    return datetime.fromisoformat(value) if value else None
