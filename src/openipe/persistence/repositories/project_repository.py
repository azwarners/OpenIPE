"""Project persistence and computed task summaries."""

from __future__ import annotations

from datetime import UTC, datetime
import sqlite3

from openipe.core.models.project import Project, ProjectStatus


class ProjectRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(self, user_id, title, description, source_inbox_item_id) -> Project:
        now = _timestamp(datetime.now(UTC))
        cursor = self.connection.execute(
            """INSERT INTO projects(user_id, title, description, status, source_inbox_item_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, title, description, ProjectStatus.ACTIVE.value, source_inbox_item_id, now, now),
        )
        self.connection.commit()
        return self.get(user_id, cursor.lastrowid)

    def get(self, user_id: int, project_id: int) -> Project | None:
        row = self.connection.execute(
            "SELECT * FROM projects WHERE user_id = ? AND id = ?", (user_id, project_id)
        ).fetchone()
        return _to_project(row) if row else None

    def list(self, user_id: int, status: ProjectStatus | None = None) -> list[Project]:
        query = "SELECT * FROM projects WHERE user_id = ?"
        params: list[object] = [user_id]
        if status is not None:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY created_at DESC, id DESC"
        return [_to_project(row) for row in self.connection.execute(query, params).fetchall()]

    def update(self, user_id, project_id, title, description, status, next_action_task_id,
               source_inbox_item_id, completed_at, archived_at) -> Project | None:
        self.connection.execute(
            """UPDATE projects SET title = ?, description = ?, status = ?, next_action_task_id = ?,
            source_inbox_item_id = ?, updated_at = ?, completed_at = ?, archived_at = ?
            WHERE user_id = ? AND id = ?""",
            (title, description, status.value, next_action_task_id, source_inbox_item_id,
             _timestamp(datetime.now(UTC)), _timestamp(completed_at) if completed_at else None,
             _timestamp(archived_at) if archived_at else None, user_id, project_id),
        )
        self.connection.commit()
        return self.get(user_id, project_id)

    def clear_next_action_for_task(self, user_id: int, task_id: int) -> None:
        self.connection.execute(
            "UPDATE projects SET next_action_task_id = NULL, updated_at = ? WHERE user_id = ? AND next_action_task_id = ?",
            (_timestamp(datetime.now(UTC)), user_id, task_id),
        )
        self.connection.commit()

    def set_next_action(self, user_id: int, project_id: int, task_id: int) -> Project | None:
        self.connection.execute(
            "UPDATE projects SET next_action_task_id = ?, updated_at = ? WHERE user_id = ? AND id = ?",
            (task_id, _timestamp(datetime.now(UTC)), user_id, project_id),
        )
        self.connection.commit()
        return self.get(user_id, project_id)

    def task_ids(self, user_id: int, project_id: int) -> list[int]:
        rows = self.connection.execute(
            "SELECT id FROM tasks WHERE user_id = ? AND project_id = ? ORDER BY id", (user_id, project_id)
        ).fetchall()
        return [row[0] for row in rows]

    def progress(self, user_id: int, project_id: int) -> tuple[int, int, int]:
        row = self.connection.execute(
            """SELECT COUNT(*), SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END)
            FROM tasks WHERE user_id = ? AND project_id = ?""", (user_id, project_id)
        ).fetchone()
        return row[0], row[1] or 0, row[2] or 0


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _to_project(row: sqlite3.Row) -> Project:
    return Project(row["id"], row["user_id"], row["title"], row["description"],
                   ProjectStatus(row["status"]), row["next_action_task_id"],
                   row["source_inbox_item_id"], datetime.fromisoformat(row["created_at"]),
                   datetime.fromisoformat(row["updated_at"]), _parse(row["completed_at"]),
                   _parse(row["archived_at"]))


def _parse(value):
    return datetime.fromisoformat(value) if value else None
