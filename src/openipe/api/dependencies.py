"""FastAPI dependencies for database and authentication access."""

from __future__ import annotations

import sqlite3

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from openipe.application.auth_service import AuthService
from openipe.core.errors import AuthenticationError, PermissionDeniedError
from openipe.core.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_connection(request: Request) -> sqlite3.Connection:
    return request.app.state.database


async def get_auth_service(
    request: Request,
    connection: sqlite3.Connection = Depends(get_connection),
) -> AuthService:
    return AuthService(connection, request.app.state.settings)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    service: AuthService = Depends(get_auth_service),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return service.current_user(credentials.credentials)
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator permission is required")
    return user
