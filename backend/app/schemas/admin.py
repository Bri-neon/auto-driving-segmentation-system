from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AdminUserItemData(BaseModel):
    id: int
    username: str
    email: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class AdminUserListData(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminUserItemData]


class AdminUserDetailData(BaseModel):
    user: AdminUserItemData


class AdminUserUpdateRequest(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    nickname: str | None = Field(default=None, max_length=64)
    role: str | None = None
    is_active: bool | None = None


class AdminUserPasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)


class AdminUserPasswordResetData(BaseModel):
    id: int
    password_reset: bool


class AdminHistoryUpdateRequest(BaseModel):
    realtime_status: str | None = None
    finalize_status: str | None = None
    status_message: str | None = Field(default=None, max_length=255)
    segmented_url: str | None = Field(default=None, max_length=255)
    overlay_url: str | None = Field(default=None, max_length=255)
