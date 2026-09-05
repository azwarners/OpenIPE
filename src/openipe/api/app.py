"""OpenIPE composition root and compatibility application factory."""

from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI

from openipe.api.REST.app import create_app as create_rest_app
from openipe.api.internal import InternalAPI
from openipe.core.config import Settings
from openipe.persistence.database import initialize_database


def create_app(
    settings: Settings | None = None,
    connection: sqlite3.Connection | None = None,
    internal_api: InternalAPI | None = None,
) -> FastAPI:
    """Compose settings, persistence, the internal API, and the REST adapter."""
    resolved_settings = settings or Settings.from_environment()
    owns_database = connection is None
    database = connection or initialize_database(resolved_settings.database_path)
    façade = internal_api or InternalAPI(database, resolved_settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        if owns_database:
            database.close()

    return create_rest_app(façade, lifespan=lifespan)


__all__ = ["create_app"]
