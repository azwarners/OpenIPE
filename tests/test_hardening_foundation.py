"""Configuration, migration, and application-lifecycle regression coverage."""

import asyncio
import sqlite3

import pytest

from openipe.api.app import create_app
from openipe.core.config import Settings
from openipe.core.logging import configure_logging
from openipe.persistence.database import connect, initialize_database
from openipe.persistence.migrations import Migration, apply_migrations


@pytest.mark.parametrize(
    ("name", "value", "expected"),
    [
        ("OPENIPE_API_HOST", "0.0.0.0", "0.0.0.0"),
        ("OPENIPE_API_PORT", "9123", 9123),
        ("OPENIPE_TOKEN_EXPIRATION", "1", 1),
        ("OPENIPE_LOG_LEVEL", "warning", "WARNING"),
        ("OPENIPE_ALLOW_USER_CREATION", " TRUE ", True),
        ("OPENIPE_ALLOW_USER_CREATION", "0", False),
    ],
    ids=["host", "port", "token-expiration", "log-level", "boolean-true", "boolean-false"],
)
def test_supported_environment_values_are_parsed(monkeypatch, name, value, expected):
    monkeypatch.setenv(name, value)
    settings = Settings.from_environment()
    field = {
        "OPENIPE_API_HOST": "api_host",
        "OPENIPE_API_PORT": "api_port",
        "OPENIPE_TOKEN_EXPIRATION": "token_expiration",
        "OPENIPE_LOG_LEVEL": "log_level",
        "OPENIPE_ALLOW_USER_CREATION": "allow_user_creation",
    }[name]
    assert getattr(settings, field) == expected


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("OPENIPE_ALLOW_USER_CREATION", "maybe"),
        ("OPENIPE_API_PORT", "not-an-int"),
        ("OPENIPE_TOKEN_EXPIRATION", "1.5"),
    ],
    ids=["malformed-boolean", "malformed-port", "malformed-expiration"],
)
def test_malformed_environment_values_fail_during_startup(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        Settings.from_environment()


def test_empty_environment_values_preserve_defaults(monkeypatch):
    monkeypatch.setenv("OPENIPE_API_HOST", "")
    monkeypatch.setenv("OPENIPE_API_PORT", "")
    monkeypatch.setenv("OPENIPE_TOKEN_EXPIRATION", "")
    settings = Settings.from_environment()
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8000
    assert settings.token_expiration == 86_400


@pytest.mark.parametrize("level", ["debug", "INFO", "WaRnInG", "error", "critical"])
def test_supported_logging_levels_configure(level):
    configure_logging(level)


def test_connection_enables_foreign_keys_and_busy_timeout(tmp_path):
    connection = connect(tmp_path / "settings.sqlite3")
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
    finally:
        connection.close()


def test_initialize_database_is_idempotent(tmp_path):
    path = tmp_path / "repeat.sqlite3"
    first = initialize_database(path)
    first.close()
    second = initialize_database(path)
    try:
        assert second.execute("SELECT COUNT(*) FROM schema_versions").fetchone()[0] == 7
        assert second.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0] == 7
    finally:
        second.close()


def test_migrations_are_sorted_and_duplicate_versions_are_rejected():
    connection = sqlite3.connect(":memory:")
    try:
        migration = Migration(2, "later", lambda db: db.execute("CREATE TABLE later (id INTEGER)"))
        with pytest.raises(ValueError, match="unique"):
            apply_migrations(connection, [migration, Migration(2, "duplicate", lambda db: None)])
        with pytest.raises(ValueError, match="positive"):
            apply_migrations(connection, [Migration(0, "invalid", lambda db: None)])
    finally:
        connection.close()


def test_failed_migration_rolls_back_schema_and_ledger():
    connection = sqlite3.connect(":memory:")

    def fail(db):
        db.execute("CREATE TABLE transient (id INTEGER)")
        raise RuntimeError("boom")

    try:
        with pytest.raises(RuntimeError, match="boom"):
            apply_migrations(connection, [Migration(1, "fail", fail)])
        assert connection.execute("SELECT * FROM schema_versions").fetchall() == []
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE name = 'transient'"
        ).fetchone() is None
    finally:
        connection.close()


def test_composition_root_closes_only_connections_it_owns(tmp_path):
    settings = Settings(database_path=tmp_path / "owned.sqlite3")
    app = create_app(settings=settings)
    async def exercise_owned():
        async with app.router.lifespan_context(app):
            assert app.state.internal_api.connection
    asyncio.run(exercise_owned())
    with pytest.raises(sqlite3.ProgrammingError):
        app.state.internal_api.connection.execute("SELECT 1")

    injected = initialize_database(tmp_path / "injected.sqlite3")
    injected_app = create_app(settings=settings, connection=injected)
    async def exercise_injected():
        async with injected_app.router.lifespan_context(injected_app):
            assert injected.execute("SELECT 1").fetchone()[0] == 1
    asyncio.run(exercise_injected())
    try:
        assert injected.execute("SELECT 1").fetchone()[0] == 1
    finally:
        injected.close()
