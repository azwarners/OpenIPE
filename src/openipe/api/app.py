"""FastAPI application factory."""

from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI

from openipe.api.routes import auth, goals, habit_stacks, habits, inbox, projects, tasks, today, users
from openipe.core.config import Settings
from openipe.persistence.database import initialize_database


def create_app(
    settings: Settings | None = None,
    connection: sqlite3.Connection | None = None,
) -> FastAPI:
    """Create an OpenIPE Core API application."""

    resolved_settings = settings or Settings.from_environment()
    owns_database = connection is None
    database = connection or initialize_database(resolved_settings.database_path)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        if owns_database:
            database.close()

    app = FastAPI(title="OpenIPE Core", version="0.0.1", lifespan=lifespan)
    app.state.database = database
    app.state.settings = resolved_settings
    app.state.owns_database = owns_database
    app.include_router(auth.setup_router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(inbox.router, prefix="/api/v1")
    app.include_router(goals.router, prefix="/api/v1")
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(habits.router, prefix="/api/v1")
    app.include_router(habit_stacks.router, prefix="/api/v1")
    app.include_router(today.router, prefix="/api/v1")

    return app
