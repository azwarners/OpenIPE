"""Explicit, transactional SQLite migration support."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

from .schema import ensure_schema_versions_table

MigrationFunction = Callable[[sqlite3.Connection], None]


@dataclass(frozen=True, slots=True)
class Migration:
    """A single ordered database migration."""

    version: int
    name: str
    apply: MigrationFunction


def _create_users_schema(connection: sqlite3.Connection) -> None:
    for statement in (
        """CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL COLLATE NOCASE UNIQUE,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0 CHECK (is_admin IN (0, 1)),
            is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_login_at TEXT
        )""",
        """CREATE TABLE auth_tokens (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            revoked_at TEXT
        )""",
        "CREATE INDEX idx_auth_tokens_user_id ON auth_tokens(user_id)",
        "CREATE INDEX idx_auth_tokens_expires_at ON auth_tokens(expires_at)",
    ):
        connection.execute(statement)


def _create_inbox_schema(connection: sqlite3.Connection) -> None:
    for statement in (
        """CREATE TABLE inbox_items (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('unprocessed', 'processed', 'archived', 'discarded')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            processed_at TEXT,
            archived_at TEXT
        )""",
        "CREATE INDEX idx_inbox_items_user_status ON inbox_items(user_id, status)",
        "CREATE INDEX idx_inbox_items_user_created ON inbox_items(user_id, created_at)",
    ):
        connection.execute(statement)


def _create_goals_schema(connection: sqlite3.Connection) -> None:
    for statement in (
        """CREATE TABLE goals (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL CHECK (status IN ('active', 'paused', 'achieved', 'abandoned', 'archived')),
            target_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            achieved_at TEXT,
            archived_at TEXT,
            source_inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL
        )""",
        "CREATE INDEX idx_goals_user_status ON goals(user_id, status)",
        "CREATE INDEX idx_goals_user_target_date ON goals(user_id, target_date)",
    ):
        connection.execute(statement)


def _create_projects_and_tasks_schema(connection: sqlite3.Connection) -> None:
    for statement in (
        """CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL CHECK (status IN ('active', 'paused', 'completed', 'cancelled', 'archived')),
            next_action_task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
            source_inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            archived_at TEXT
        )""",
        """CREATE TABLE tasks (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            status TEXT NOT NULL CHECK (status IN ('open', 'completed', 'cancelled', 'archived')),
            priority TEXT NOT NULL CHECK (priority IN ('low', 'normal', 'high')),
            due_date TEXT,
            is_today INTEGER NOT NULL DEFAULT 0 CHECK (is_today IN (0, 1)),
            source_inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            archived_at TEXT
        )""",
        "CREATE INDEX idx_projects_user_status ON projects(user_id, status)",
        "CREATE INDEX idx_tasks_user_status ON tasks(user_id, status)",
        "CREATE INDEX idx_tasks_user_project ON tasks(user_id, project_id)",
        "CREATE INDEX idx_tasks_user_due_date ON tasks(user_id, due_date)",
        "CREATE INDEX idx_tasks_user_today ON tasks(user_id, is_today)",
    ):
        connection.execute(statement)


def _create_habits_and_checkins_schema(connection: sqlite3.Connection) -> None:
    for statement in (
        """CREATE TABLE habits (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            description TEXT,
            frequency_type TEXT NOT NULL CHECK (frequency_type IN ('daily', 'weekdays', 'selected_days', 'times_per_week')),
            frequency_config TEXT NOT NULL,
            minimum_version TEXT,
            stack_id INTEGER,
            position INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            source_inbox_item_id INTEGER REFERENCES inbox_items(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            archived_at TEXT
        )""",
        """CREATE TABLE habit_checkins (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('completed', 'skipped', 'not_done')),
            note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(habit_id, date)
        )""",
        "CREATE INDEX idx_habits_user_active ON habits(user_id, active)",
        "CREATE INDEX idx_habit_checkins_user_date ON habit_checkins(user_id, date)",
        "CREATE INDEX idx_habit_checkins_habit_date ON habit_checkins(habit_id, date)",
    ):
        connection.execute(statement)


def _create_habit_stacks_schema(connection: sqlite3.Connection) -> None:
    for statement in (
        """CREATE TABLE habit_stacks (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT,
            position INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            archived_at TEXT
        )""",
        "CREATE INDEX idx_habit_stacks_user_active ON habit_stacks(user_id, active)",
        "CREATE INDEX idx_habits_user_stack_position ON habits(user_id, stack_id, position)",
    ):
        connection.execute(statement)


def _create_goal_associations_schema(connection: sqlite3.Connection) -> None:
    for statement in (
        """CREATE TABLE goal_projects (
            goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            PRIMARY KEY (goal_id, project_id)
        )""",
        """CREATE TABLE goal_tasks (
            goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
            task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            PRIMARY KEY (goal_id, task_id)
        )""",
        """CREATE TABLE goal_habits (
            goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
            habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            PRIMARY KEY (goal_id, habit_id)
        )""",
        "CREATE INDEX idx_goal_projects_project ON goal_projects(project_id)",
        "CREATE INDEX idx_goal_tasks_task ON goal_tasks(task_id)",
        "CREATE INDEX idx_goal_habits_habit ON goal_habits(habit_id)",
    ):
        connection.execute(statement)


# Product migrations are added by their corresponding implementation phases.
MIGRATIONS: tuple[Migration, ...] = (
    Migration(1, "create_users_and_auth_tokens", _create_users_schema),
    Migration(2, "create_inbox_items", _create_inbox_schema),
    Migration(3, "create_goals", _create_goals_schema),
    Migration(4, "create_projects_and_tasks", _create_projects_and_tasks_schema),
    Migration(5, "create_habits_and_checkins", _create_habits_and_checkins_schema),
    Migration(6, "create_habit_stacks", _create_habit_stacks_schema),
    Migration(7, "create_goal_associations", _create_goal_associations_schema),
)


def apply_migrations(
    connection: sqlite3.Connection,
    migrations: Iterable[Migration] = MIGRATIONS,
) -> int:
    """Apply pending migrations and return the resulting schema version."""

    ensure_schema_versions_table(connection)
    ordered = sorted(migrations, key=lambda migration: migration.version)
    versions = [migration.version for migration in ordered]
    if len(versions) != len(set(versions)):
        raise ValueError("Migration versions must be unique")
    if any(version < 1 for version in versions):
        raise ValueError("Migration versions must be positive")

    applied = {
        row[0]
        for row in connection.execute("SELECT version FROM schema_versions")
    }
    for migration in ordered:
        if migration.version in applied:
            continue
        connection.execute("BEGIN")
        try:
            migration.apply(connection)
            connection.execute(
                "INSERT INTO schema_versions(version, name, applied_at) VALUES (?, ?, ?)",
                (migration.version, migration.name, datetime.now(UTC).isoformat()),
            )
        except Exception:
            connection.rollback()
            raise
        else:
            connection.commit()

    row = connection.execute("SELECT MAX(version) FROM schema_versions").fetchone()
    return int(row[0] or 0)
