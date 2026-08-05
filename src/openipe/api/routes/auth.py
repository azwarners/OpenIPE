"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from openipe.api.dependencies import get_auth_service, get_current_user
from openipe.api.schemas.auth import (
    ChangePasswordRequest,
    Credentials,
    InitialAdminRequest,
    LoginResponse,
    UserResponse,
)
from openipe.application.auth_service import AuthService
from openipe.core.errors import AuthenticationError, InactiveUserError, ValidationError
from openipe.core.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])
setup_router = APIRouter(prefix="/setup", tags=["setup"])
bearer_scheme = HTTPBearer(auto_error=False)


@setup_router.post("/initial-admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_initial_admin(request: InitialAdminRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return _public_user(service.create_initial_admin(request.username, request.display_name, request.password))
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/login", response_model=LoginResponse)
async def login(request: Credentials, service: AuthService = Depends(get_auth_service)):
    try:
        user, token, expires_at = service.login(request.username, request.password)
    except InactiveUserError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return LoginResponse(access_token=token, expires_at=expires_at, user=_public_user(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    service: AuthService = Depends(get_auth_service),
):
    if credentials is not None and credentials.scheme.lower() == "bearer":
        service.logout(credentials.credentials)


@router.get("/me", response_model=UserResponse)
async def current_user(user: User = Depends(get_current_user)):
    return _public_user(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    try:
        service.change_password(user, request.current_password, request.new_password)
    except (AuthenticationError, ValidationError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


def _public_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        is_admin=user.is_admin,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )
