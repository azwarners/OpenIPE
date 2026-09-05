"""HTTP translation for authentication operations."""
from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from openipe.api.REST.dependencies import get_current_user, get_internal_api
from openipe.api.REST.schemas.auth import ChangePasswordRequest, Credentials, InitialAdminRequest, LoginResponse, UserResponse
from openipe.api.internal import InternalAPI, InternalContext
from openipe.api.internal.contracts import ChangePasswordContract, CredentialsContract, InitialAdminContract
from openipe.api.internal.errors import InternalAuthenticationError as AuthenticationError, InternalInactiveUserError as InactiveUserError, InternalValidationError as ValidationError

router=APIRouter(prefix="/auth",tags=["authentication"]); setup_router=APIRouter(prefix="/setup",tags=["setup"]); bearer_scheme=HTTPBearer(auto_error=False)
def _user(x): return UserResponse.model_validate(asdict(x))

@setup_router.post("/initial-admin",response_model=UserResponse,status_code=201)
async def create_initial_admin(request:InitialAdminRequest, internal:InternalAPI=Depends(get_internal_api)):
    try: return _user(internal.auth.initial_admin(InitialAdminContract(request.username,request.display_name,request.password)))
    except ValidationError as e: raise HTTPException(409,str(e)) from e

@router.post("/login",response_model=LoginResponse)
async def login(request:Credentials,internal:InternalAPI=Depends(get_internal_api)):
    try: result=internal.auth.login(CredentialsContract(request.username,request.password))
    except InactiveUserError as e: raise HTTPException(403,str(e)) from e
    except AuthenticationError as e: raise HTTPException(401,str(e),headers={"WWW-Authenticate":"Bearer"}) from e
    return LoginResponse(access_token=result.access_token,expires_at=result.expires_at,user=_user(result.user))

@router.post("/logout",status_code=204)
async def logout(credentials:HTTPAuthorizationCredentials|None=Depends(bearer_scheme),internal:InternalAPI=Depends(get_internal_api)):
    if credentials is not None and credentials.scheme.lower()=="bearer": internal.auth.logout(credentials.credentials)

@router.get("/me",response_model=UserResponse)
async def current_user(context:InternalContext=Depends(get_current_user),internal:InternalAPI=Depends(get_internal_api)): return _user(internal.auth.current_user(context))

@router.post("/change-password",status_code=204)
async def change_password(request:ChangePasswordRequest,context:InternalContext=Depends(get_current_user),internal:InternalAPI=Depends(get_internal_api)):
    try: internal.auth.change_password(context,ChangePasswordContract(request.current_password,request.new_password))
    except (AuthenticationError,ValidationError) as e: raise HTTPException(400,str(e)) from e
