"""FastAPI HTTP adapter factory."""

from fastapi import FastAPI

from openipe.api.REST.routes import auth, goals, habit_stacks, habits, inbox, projects, tasks, today, users
from openipe.api.internal import InternalAPI


def create_app(internal_api: InternalAPI, lifespan=None) -> FastAPI:
    """Create the HTTP adapter around an already-constructed internal API."""
    app = FastAPI(title="OpenIPE Core", version="0.0.1", lifespan=lifespan)
    app.state.internal_api = internal_api
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
