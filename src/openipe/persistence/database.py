"""SQLite connection and initialization helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from .migrations import MIGRATIONS, Migration, apply_migrations


def connect(database_path: str | Path) -> sqlite3.Connection:
    """Open a configured SQLite connection with foreign keys enabled."""

    # FastAPI may execute synchronous dependencies and routes in worker
    # threads. Repository calls remain serialized by the application layer,
    # while SQLite's connection is permitted to be used by those workers.
    connection = sqlite3.connect(str(database_path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize_database(
    database_path: str | Path,
    migrations: Iterable[Migration] = MIGRATIONS,
) -> sqlite3.Connection:
    """Open and initialize a database, leaving the connection open to callers."""

    path = Path(database_path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(path)
    try:
        apply_migrations(connection, migrations)
    except Exception:
        connection.close()
        raise
    return connection
