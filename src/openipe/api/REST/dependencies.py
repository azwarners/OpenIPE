"""HTTP dependencies for façade access and bearer authentication."""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from openipe.api.internal import InternalAPI, InternalContext
from openipe.api.internal.errors import InternalAuthenticationError, InternalPermissionDeniedError

bearer_scheme = HTTPBearer(auto_error=False)


async def get_internal_api(request: Request) -> InternalAPI:
    return request.app.state.internal_api


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    internal: InternalAPI = Depends(get_internal_api),
) -> InternalContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return internal.authenticate(credentials.credentials)
    except InternalAuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


async def require_admin(
    context: InternalContext = Depends(get_current_user),
    internal: InternalAPI = Depends(get_internal_api),
) -> InternalContext:
    try:
        return internal.authorize_admin(context)
    except InternalPermissionDeniedError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
