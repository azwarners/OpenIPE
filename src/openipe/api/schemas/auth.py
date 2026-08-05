"""Authentication API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class Credentials(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class InitialAdminRequest(Credentials):
    display_name: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: "UserResponse"


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=1)


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    password: str = Field(min_length=1)
    is_admin: bool = False


class UserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None


LoginResponse.model_rebuild()
