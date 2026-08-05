"""Shared test configuration."""

from pathlib import Path


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "phase1: tests for the Phase 1 foundation")


def temporary_database_path(tmp_path: Path) -> Path:
    """Return a database path within pytest's isolated temporary directory."""

    return tmp_path / "openipe-test.sqlite3"
