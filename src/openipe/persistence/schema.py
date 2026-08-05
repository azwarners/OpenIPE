"""Bootstrap schema for the OpenIPE database."""

from __future__ import annotations

import sqlite3


def ensure_schema_versions_table(connection: sqlite3.Connection) -> None:
    """Create the migration ledger if it does not already exist."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_versions (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )
