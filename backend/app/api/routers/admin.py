from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, require_admin
from app.core.exceptions import AppException
from app.core.responses import success_response
from app.schemas.admin import (
    AdminHistoryUpdateRequest,
    AdminUserDetailData,
    AdminUserItemData,
    AdminUserListData,
    AdminUserPasswordResetData,
    AdminUserPasswordResetRequest,
    AdminUserUpdateRequest,
)
from app.schemas.common import ApiResponse
from app.schemas.history import InferenceHistoryDeleteData, InferenceHistoryDetailData, InferenceHistoryItemData, InferenceHistoryListData
from app.services.history_service import inference_history_service
from app.services.user_service import user_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=ApiResponse[AdminUserListData])
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None),
    role: str | None = Query(default=None, description="admin/user"),
    is_active: bool | None = Query(default=None),
    _admin: CurrentUser = Depends(require_admin),
) -> ApiResponse[AdminUserListData]:
    total, rows = user_service.admin_list_users(
        page=page,
        page_size=page_size,
        keyword=keyword,
        role=role,
        is_active=is_active,
    )
    return success_response(
        AdminUserListData(
            total=total,
            page=page,
            page_size=page_size,
            items=[AdminUserItemData(**row) for row in rows],
        )
    )


@router.get("/users/{user_id}", response_model=ApiResponse[AdminUserDetailData])
async def get_user_detail(
    user_id: int,
    _admin: CurrentUser = Depends(require_admin),
) -> ApiResponse[AdminUserDetailData]:
    row = user_service.get_user_by_id(user_id)
    if row is None:
        raise AppException("用户不存在", status_code=HTTPStatus.NOT_FOUND)
    return success_response(AdminUserDetailData(user=AdminUserItemData(**row)))


@router.patch("/users/{user_id}", response_model=ApiResponse[AdminUserDetailData])
async def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    admin_user: CurrentUser = Depends(require_admin),
) -> ApiResponse[AdminUserDetailData]:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise AppException("缺少可更新字段", status_code=HTTPStatus.BAD_REQUEST)

    if int(admin_user["id"]) == user_id:
        if updates.get("role") == "user":
            raise AppException("不允许将当前管理员降级", status_code=HTTPStatus.BAD_REQUEST)
        if updates.get("is_active") is False:
            raise AppException("不允许禁用当前管理员账号", status_code=HTTPStatus.BAD_REQUEST)

    updated = user_service.admin_update_user(user_id, updates)
    if updated is None:
        raise AppException("用户不存在", status_code=HTTPStatus.NOT_FOUND)
    return success_response(AdminUserDetailData(user=AdminUserItemData(**updated)))


@router.put("/users/{user_id}/password", response_model=ApiResponse[AdminUserPasswordResetData])
async def reset_user_password(
    user_id: int,
    payload: AdminUserPasswordResetRequest,
    _admin: CurrentUser = Depends(require_admin),
) -> ApiResponse[AdminUserPasswordResetData]:
    if user_service.get_user_by_id(user_id) is None:
        raise AppException("用户不存在", status_code=HTTPStatus.NOT_FOUND)
    user_service.admin_reset_user_password(user_id, payload.new_password)
    return success_response(AdminUserPasswordResetData(id=user_id, password_reset=True))


@router.get("/histories", response_model=ApiResponse[InferenceHistoryListData])
async def list_all_histories(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    request_type: str | None = Query(default=None, description="image/video"),
    process_mode: str | None = Query(default=None, description="sync/realtime"),
    user_id: int | None = Query(default=None, ge=1),
    username: str | None = Query(default=None),
    _admin: CurrentUser = Depends(require_admin),
) -> ApiResponse[InferenceHistoryListData]:
    if request_type and request_type not in {"image", "video"}:
        raise AppException("request_type 仅支持 image/video", status_code=HTTPStatus.BAD_REQUEST)
    if process_mode and process_mode not in {"sync", "realtime"}:
        raise AppException("process_mode 仅支持 sync/realtime", status_code=HTTPStatus.BAD_REQUEST)

    total, rows = inference_history_service.list_admin_histories(
        page=page,
        page_size=page_size,
        request_type=request_type,
        process_mode=process_mode,
        user_id=user_id,
        username=username,
    )
    return success_response(
        InferenceHistoryListData(
            total=total,
            page=page,
            page_size=page_size,
            items=[InferenceHistoryItemData(**row) for row in rows],
        )
    )


@router.get("/histories/{history_id}", response_model=ApiResponse[InferenceHistoryDetailData])
async def get_history_detail(
    history_id: int,
    _admin: CurrentUser = Depends(require_admin),
) -> ApiResponse[InferenceHistoryDetailData]:
    row = inference_history_service.get_history_by_id(history_id, include_user_meta=True)
    if row is None:
        raise AppException("历史记录不存在", status_code=HTTPStatus.NOT_FOUND)
    return success_response(InferenceHistoryDetailData(item=InferenceHistoryItemData(**row)))


@router.patch("/histories/{history_id}", response_model=ApiResponse[InferenceHistoryDetailData])
async def update_history(
    history_id: int,
    payload: AdminHistoryUpdateRequest,
    _admin: CurrentUser = Depends(require_admin),
) -> ApiResponse[InferenceHistoryDetailData]:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise AppException("缺少可更新字段", status_code=HTTPStatus.BAD_REQUEST)
    row = inference_history_service.admin_update_history(history_id, updates)
    if row is None:
        raise AppException("历史记录不存在", status_code=HTTPStatus.NOT_FOUND)
    return success_response(InferenceHistoryDetailData(item=InferenceHistoryItemData(**row)))


@router.delete("/histories/{history_id}", response_model=ApiResponse[InferenceHistoryDeleteData])
async def delete_history(
    history_id: int,
    _admin: CurrentUser = Depends(require_admin),
) -> ApiResponse[InferenceHistoryDeleteData]:
    deleted = inference_history_service.delete_history_by_id(history_id)
    if not deleted:
        raise AppException("历史记录不存在", status_code=HTTPStatus.NOT_FOUND)
    return success_response(InferenceHistoryDeleteData(id=history_id, deleted=True))
