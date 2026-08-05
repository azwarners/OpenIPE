"""Administrator user-management routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from openipe.api.dependencies import get_auth_service, require_admin
from openipe.api.routes.auth import _public_user
from openipe.api.schemas.auth import UserCreateRequest, UserResponse, UserUpdateRequest
from openipe.application.auth_service import AuthService
from openipe.core.errors import NotFoundError, PermissionDeniedError, ValidationError
from openipe.core.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def list_users(actor: User = Depends(require_admin), service: AuthService = Depends(get_auth_service)):
    return [_public_user(user) for user in service.list_users(actor)]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    actor: User = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    try:
        return _public_user(service.create_user(actor, request.username, request.display_name, request.password, request.is_admin))
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    actor: User = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    try:
        return _public_user(service.get_user(actor, user_id))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found") from error


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    actor: User = Depends(require_admin),
    service: AuthService = Depends(get_auth_service),
):
    try:
        target = service.get_user(actor, user_id)
        if request.display_name is not None:
            if not request.display_name.strip():
                raise ValidationError("Display name must not be empty")
            service.users.update_display_name(user_id, request.display_name.strip())
        if request.is_active is not None:
            target = service.set_active(actor, user_id, request.is_active)
        return _public_user(service.get_user(actor, user_id))
    except NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found") from error
    except (PermissionDeniedError, ValidationError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
