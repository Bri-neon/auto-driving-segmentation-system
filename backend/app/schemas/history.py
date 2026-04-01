from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class InferenceHistoryItemData(BaseModel):
    id: int
    user_id: int | None = None
    user_username: str | None = None
    user_nickname: str | None = None
    task_id: str | None = None
    request_type: str
    process_mode: str
    model_key: str
    model_name: str
    resolution: str | None = None
    original_url: str
    segmented_url: str | None = None
    overlay_url: str | None = None
    realtime_status: str
    finalize_status: str
    status_message: str | None = None
    avg_fps: float | None = None
    realtime_fps: float | None = None
    inference_time: float | None = None
    classes: list[dict[str, Any]] | None = None
    created_at: datetime
    updated_at: datetime


class InferenceHistoryListData(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[InferenceHistoryItemData]


class InferenceHistoryDetailData(BaseModel):
    item: InferenceHistoryItemData


class InferenceHistoryDeleteData(BaseModel):
    id: int
    deleted: bool
