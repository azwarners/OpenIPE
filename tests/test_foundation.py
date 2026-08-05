import sqlite3

import pytest

from openipe import __version__
from openipe.core.config import Settings
from openipe.core.logging import configure_logging
from openipe.persistence.database import initialize_database
from openipe.persistence.migrations import Migration, apply_migrations


@pytest.mark.phase1
def test_package_exposes_version() -> None:
    assert __version__ == "0.0.1"


@pytest.mark.phase1
def test_settings_defaults_and_environment(monkeypatch) -> None:
    defaults = Settings()
    assert defaults.database_path.name == "openipe.sqlite3"
    assert defaults.api_host == "127.0.0.1"
    assert defaults.api_port == 8000
    assert defaults.allow_user_creation is False

    monkeypatch.setenv("OPENIPE_DATABASE_PATH", "/tmp/custom.sqlite3")
    monkeypatch.setenv("OPENIPE_API_PORT", "9000")
    monkeypatch.setenv("OPENIPE_ALLOW_USER_CREATION", "yes")
    settings = Settings.from_environment()
    assert str(settings.database_path) == "/tmp/custom.sqlite3"
    assert settings.api_port == 9000
    assert settings.allow_user_creation is True


@pytest.mark.phase1
def test_invalid_boolean_configuration_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("OPENIPE_ALLOW_USER_CREATION", "sometimes")
    with pytest.raises(ValueError, match="must be a boolean"):
        Settings.from_environment()


@pytest.mark.phase1
def test_logging_rejects_unknown_level() -> None:
    with pytest.raises(ValueError, match="Unknown log level"):
        configure_logging("not-a-level")


@pytest.mark.phase1
def test_database_initializes_schema_version_table(tmp_path) -> None:
    connection = initialize_database(tmp_path / "nested" / "openipe.sqlite3")
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_versions'"
        ).fetchone()[0] == "schema_versions"
        assert connection.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0] == 7
    finally:
        connection.close()


@pytest.mark.phase1
def test_migrations_are_applied_once_and_recorded() -> None:
    connection = sqlite3.connect(":memory:")
    calls: list[str] = []

    def create_probe(database: sqlite3.Connection) -> None:
        calls.append("probe")
        database.execute("CREATE TABLE probe (id INTEGER PRIMARY KEY)")

    migration = Migration(1, "create_probe", create_probe)
    assert apply_migrations(connection, [migration]) == 1
    assert apply_migrations(connection, [migration]) == 1
    assert calls == ["probe"]
    assert connection.execute(
        "SELECT version, name FROM schema_versions"
    ).fetchone() == (1, "create_probe")


@pytest.mark.phase1
def test_failed_migration_is_rolled_back() -> None:
    connection = sqlite3.connect(":memory:")

    def fail(database: sqlite3.Connection) -> None:
        database.execute("CREATE TABLE transient (id INTEGER)")
        raise RuntimeError("migration failed")

    with pytest.raises(RuntimeError, match="migration failed"):
        apply_migrations(connection, [Migration(1, "failing", fail)])

    assert connection.execute(
        "SELECT version FROM schema_versions"
    ).fetchall() == []
    assert connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'transient'"
    ).fetchone() is None
