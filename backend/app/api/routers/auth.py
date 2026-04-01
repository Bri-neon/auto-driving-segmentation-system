from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.api.deps import CurrentUser, get_current_user
from app.core.config import AVATAR_DIR, settings
from app.core.exceptions import AppException
from app.core.responses import success_response
from app.core.security import create_access_token, verify_password
from app.schemas.auth import (
    AvatarUploadData,
    LoginData,
    LoginRequest,
    MeData,
    PasswordChangeData,
    PasswordChangeRequest,
    ProfileUpdateData,
    ProfileUpdateRequest,
    RegisterData,
    RegisterRequest,
    UserPublicData,
)
from app.schemas.common import ApiResponse
from app.services.user_service import user_service
from app.utils.file_utils import build_unique_filename, save_upload_file, validate_upload_file

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_public_data(row: dict) -> UserPublicData:
    return UserPublicData(
        id=int(row["id"]),
        username=str(row["username"]),
        email=row.get("email"),
        nickname=row.get("nickname"),
        avatar_url=row.get("avatar_url"),
        role=str(row.get("role", "user")),
        is_active=bool(row.get("is_active", 0)),
        created_at=row["created_at"],
        last_login_at=row.get("last_login_at"),
    )


def _cleanup_old_avatar(old_avatar_url: str | None) -> None:
    if not old_avatar_url:
        return
    prefix = f"{settings.static_url_prefix}/avatar/"
    if not old_avatar_url.startswith(prefix):
        return

    filename = old_avatar_url[len(prefix) :]
    if not filename or "/" in filename or "\\" in filename:
        return

    old_path = AVATAR_DIR / filename
    try:
        if old_path.exists() and old_path.resolve().parent == AVATAR_DIR.resolve():
            old_path.unlink(missing_ok=True)
    except OSError:
        return


@router.post("/register", response_model=ApiResponse[RegisterData], status_code=HTTPStatus.CREATED)
async def register(payload: RegisterRequest) -> ApiResponse[RegisterData]:
    created = user_service.create_user(
        username=payload.username,
        password=payload.password,
        email=payload.email,
        nickname=payload.nickname,
    )
    return success_response(RegisterData(user=_to_user_public_data(created)))


@router.post("/login", response_model=ApiResponse[LoginData])
async def login(request: Request, payload: LoginRequest) -> ApiResponse[LoginData]:
    user_with_hash = user_service.get_user_by_username(payload.username)
    login_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    if user_with_hash is None:
        user_service.record_login_log(
            user_id=None,
            is_success=False,
            reason="user_not_found",
            login_ip=login_ip,
            user_agent=user_agent,
        )
        raise AppException("用户名或密码错误", status_code=HTTPStatus.UNAUTHORIZED)

    user_id = int(user_with_hash["id"])
    if not verify_password(payload.password, str(user_with_hash.get("password_hash", ""))):
        user_service.record_login_log(
            user_id=user_id,
            is_success=False,
            reason="password_invalid",
            login_ip=login_ip,
            user_agent=user_agent,
        )
        raise AppException("用户名或密码错误", status_code=HTTPStatus.UNAUTHORIZED)

    if not bool(user_with_hash.get("is_active", 0)):
        user_service.record_login_log(
            user_id=user_id,
            is_success=False,
            reason="user_disabled",
            login_ip=login_ip,
            user_agent=user_agent,
        )
        raise AppException("用户已被禁用", status_code=HTTPStatus.FORBIDDEN)

    user_service.update_last_login(user_id)
    user_service.record_login_log(
        user_id=user_id,
        is_success=True,
        reason=None,
        login_ip=login_ip,
        user_agent=user_agent,
    )

    user_row = user_service.get_user_by_id(user_id)
    if user_row is None:
        raise AppException("用户不存在", status_code=HTTPStatus.UNAUTHORIZED)

    token, expires_in = create_access_token(
        user_id=user_id,
        username=str(user_row["username"]),
        role=str(user_row.get("role", "user")),
    )

    return success_response(
        LoginData(
            access_token=token,
            token_type="Bearer",
            expires_in=expires_in,
            user=_to_user_public_data(user_row),
        )
    )


@router.get("/me", response_model=ApiResponse[MeData])
async def get_me(current_user: CurrentUser = Depends(get_current_user)) -> ApiResponse[MeData]:
    return success_response(MeData(user=_to_user_public_data(current_user)))


@router.put("/me/profile", response_model=ApiResponse[ProfileUpdateData])
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ProfileUpdateData]:
    updated = user_service.update_profile(
        user_id=int(current_user["id"]),
        email=payload.email,
        nickname=payload.nickname,
    )
    if updated is None:
        raise AppException("用户不存在", status_code=HTTPStatus.NOT_FOUND)
    return success_response(ProfileUpdateData(user=_to_user_public_data(updated)))


@router.put("/me/password", response_model=ApiResponse[PasswordChangeData])
async def change_password(
    payload: PasswordChangeRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[PasswordChangeData]:
    user_service.change_password(
        user_id=int(current_user["id"]),
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return success_response(PasswordChangeData(changed=True))


@router.post("/avatar", response_model=ApiResponse[AvatarUploadData])
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[AvatarUploadData]:
    if not file.filename:
        raise AppException("缺少文件名", status_code=HTTPStatus.BAD_REQUEST)

    validate_upload_file(file, "image")

    filename = build_unique_filename(file.filename, prefix=f"u{current_user['id']}_avatar")
    target_path = AVATAR_DIR / filename
    await save_upload_file(file, target_path)

    avatar_url = f"{settings.static_url_prefix}/avatar/{filename}"
    previous_avatar = current_user.get("avatar_url")
    updated = user_service.update_avatar(int(current_user["id"]), avatar_url)
    if updated is None:
        raise AppException("更新头像失败", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

    if previous_avatar and previous_avatar != avatar_url:
        _cleanup_old_avatar(previous_avatar)

    return success_response(AvatarUploadData(avatar_url=avatar_url))
