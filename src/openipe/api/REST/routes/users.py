"""HTTP translation for administrator user management."""
from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException
from openipe.api.REST.dependencies import get_internal_api, require_admin
from openipe.api.REST.schemas.auth import UserCreateRequest, UserResponse, UserUpdateRequest
from openipe.api.internal import InternalAPI, InternalContext
from openipe.api.internal.contracts import UserCreateContract, UserUpdateContract
from openipe.api.internal.errors import InternalNotFoundError as NotFoundError, InternalPermissionDeniedError as PermissionDeniedError, InternalValidationError as ValidationError
router=APIRouter(prefix="/users",tags=["users"])
def _user(x): return UserResponse.model_validate(asdict(x))
@router.get("",response_model=list[UserResponse])
async def list_users(context:InternalContext=Depends(require_admin),internal:InternalAPI=Depends(get_internal_api)): return [_user(x) for x in internal.users.list(context)]
@router.post("",response_model=UserResponse,status_code=201)
async def create_user(request:UserCreateRequest,context:InternalContext=Depends(require_admin),internal:InternalAPI=Depends(get_internal_api)):
    try: return _user(internal.users.create(context,UserCreateContract(request.username,request.display_name,request.password,request.is_admin)))
    except ValidationError as e: raise HTTPException(400,str(e)) from e
@router.get("/{user_id}",response_model=UserResponse)
async def get_user(user_id:int,context:InternalContext=Depends(require_admin),internal:InternalAPI=Depends(get_internal_api)):
    try: return _user(internal.users.get(context,user_id))
    except NotFoundError as e: raise HTTPException(404,"User not found") from e
@router.patch("/{user_id}",response_model=UserResponse)
async def update_user(user_id:int,request:UserUpdateRequest,context:InternalContext=Depends(require_admin),internal:InternalAPI=Depends(get_internal_api)):
    try:
        fields=request.model_fields_set
        return _user(internal.users.update(context,user_id,UserUpdateContract(request.display_name,request.is_active,frozenset(fields))))
    except NotFoundError as e: raise HTTPException(404,"User not found") from e
    except (PermissionDeniedError,ValidationError) as e: raise HTTPException(400,str(e)) from e
