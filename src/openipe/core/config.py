"""Application configuration loaded from explicit defaults and environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuration shared by the OpenIPE Core server."""

    database_path: Path = Path("openipe.sqlite3")
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    token_expiration: int = 86_400
    log_level: str = "INFO"
    allow_user_creation: bool = False

    @classmethod
    def from_environment(cls) -> "Settings":
        """Build settings from ``OPENIPE_*`` variables.

        Invalid values fail during startup rather than being silently replaced
        with defaults.
        """

        values: dict[str, object] = {}
        if value := os.getenv("OPENIPE_DATABASE_PATH"):
            values["database_path"] = Path(value)
        if value := os.getenv("OPENIPE_API_HOST"):
            values["api_host"] = value
        if value := os.getenv("OPENIPE_API_PORT"):
            values["api_port"] = int(value)
        if value := os.getenv("OPENIPE_TOKEN_EXPIRATION"):
            values["token_expiration"] = int(value)
        if value := os.getenv("OPENIPE_LOG_LEVEL"):
            values["log_level"] = value.upper()
        if value := os.getenv("OPENIPE_ALLOW_USER_CREATION"):
            normalized = value.strip().lower()
            if normalized not in {"true", "false", "1", "0", "yes", "no"}:
                raise ValueError("OPENIPE_ALLOW_USER_CREATION must be a boolean")
            values["allow_user_creation"] = normalized in {"true", "1", "yes"}
        return cls(**values)
