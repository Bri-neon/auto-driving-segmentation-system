from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserPublicData(BaseModel):
    id: int
    username: str
    email: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=8, max_length=128)
    email: str | None = Field(default=None, max_length=255)
    nickname: str | None = Field(default=None, max_length=64)


class RegisterData(BaseModel):
    user: UserPublicData


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=1, max_length=128)


class LoginData(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserPublicData


class MeData(BaseModel):
    user: UserPublicData


class AvatarUploadData(BaseModel):
    avatar_url: str


class ProfileUpdateRequest(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    nickname: str | None = Field(default=None, max_length=64)


class ProfileUpdateData(BaseModel):
    user: UserPublicData


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordChangeData(BaseModel):
    changed: bool = True
