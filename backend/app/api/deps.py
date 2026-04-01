from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from typing import Any, TypedDict

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.services.user_service import user_service


class CurrentUser(TypedDict):
    id: int
    username: str
    email: str | None
    nickname: str | None
    avatar_url: str | None
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


bearer_scheme = HTTPBearer(auto_error=False)


def normalize_user_row(row: dict[str, Any]) -> CurrentUser:
    return {
        "id": int(row["id"]),
        "username": str(row["username"]),
        "email": row.get("email"),
        "nickname": row.get("nickname"),
        "avatar_url": row.get("avatar_url"),
        "role": str(row.get("role", "user")),
        "is_active": bool(row.get("is_active", 0)),
        "created_at": row["created_at"],
        "last_login_at": row.get("last_login_at"),
    }


def parse_user_from_token(token: str) -> CurrentUser:
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", "0"))
    except Exception as ex:
        raise AppException("登录状态无效，请重新登录", status_code=HTTPStatus.UNAUTHORIZED) from ex

    user = user_service.get_user_by_id(user_id)
    if user is None:
        raise AppException("用户不存在", status_code=HTTPStatus.UNAUTHORIZED)

    current_user = normalize_user_row(user)
    if not current_user["is_active"]:
        raise AppException("用户已被禁用", status_code=HTTPStatus.FORBIDDEN)
    return current_user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise AppException("请先登录", status_code=HTTPStatus.UNAUTHORIZED)
    return parse_user_from_token(credentials.credentials)


async def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.get("role") != "admin":
        raise AppException("需要管理员权限", status_code=HTTPStatus.FORBIDDEN)
    return current_user
