from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, get_current_user
from app.core.exceptions import AppException
from app.core.responses import success_response
from app.schemas.common import ApiResponse
from app.schemas.history import (
    InferenceHistoryDeleteData,
    InferenceHistoryDetailData,
    InferenceHistoryItemData,
    InferenceHistoryListData,
)
from app.services.history_service import inference_history_service

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=ApiResponse[InferenceHistoryListData])
async def list_histories(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    request_type: str | None = Query(default=None, description="image/video"),
    process_mode: str | None = Query(default=None, description="sync/realtime"),
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[InferenceHistoryListData]:
    if request_type and request_type not in {"image", "video"}:
        raise AppException("request_type 仅支持 image/video", status_code=HTTPStatus.BAD_REQUEST)
    if process_mode and process_mode not in {"sync", "realtime"}:
        raise AppException("process_mode 仅支持 sync/realtime", status_code=HTTPStatus.BAD_REQUEST)

    total, rows = inference_history_service.list_user_histories(
        user_id=int(current_user["id"]),
        page=page,
        page_size=page_size,
        request_type=request_type,
        process_mode=process_mode,
    )

    data = InferenceHistoryListData(
        total=total,
        page=page,
        page_size=page_size,
        items=[InferenceHistoryItemData(**row) for row in rows],
    )
    return success_response(data)


@router.get("/{history_id}", response_model=ApiResponse[InferenceHistoryDetailData])
async def get_history_detail(
    history_id: int,
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[InferenceHistoryDetailData]:
    row = inference_history_service.get_user_history(
        user_id=int(current_user["id"]),
        history_id=history_id,
    )
    if row is None:
        raise AppException("历史记录不存在", status_code=HTTPStatus.NOT_FOUND)

    return success_response(InferenceHistoryDetailData(item=InferenceHistoryItemData(**row)))


@router.delete("/{history_id}", response_model=ApiResponse[InferenceHistoryDeleteData])
async def delete_history(
    history_id: int,
    current_user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[InferenceHistoryDeleteData]:
    deleted = inference_history_service.delete_user_history(
        user_id=int(current_user["id"]),
        history_id=history_id,
    )
    if not deleted:
        raise AppException("历史记录不存在", status_code=HTTPStatus.NOT_FOUND)

    return success_response(InferenceHistoryDeleteData(id=history_id, deleted=True))
