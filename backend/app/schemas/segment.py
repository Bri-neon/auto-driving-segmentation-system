from __future__ import annotations

from pydantic import BaseModel


class SegmentClassItem(BaseModel):
    name: str
    color: str
    ratio: float


class SegmentImageData(BaseModel):
    original_image_url: str
    segmented_image_url: str
    overlay_image_url: str
    inference_time: float
    model_name: str
    input_size: list[int]
    classes: list[SegmentClassItem]


class SegmentVideoData(BaseModel):
    original_video_url: str
    segmented_video_url: str
    overlay_video_url: str
    avg_fps: float
    realtime_fps: float
    inference_time: float
    model_name: str
    input_size: list[int]


class SegmentVideoRealtimeInitData(BaseModel):
    task_id: str
    ws_url: str
    status: str
    finalize_status: str
    original_video_url: str
    segmented_video_url: str
    overlay_video_url: str
    model_name: str
    input_size: list[int]


class SegmentVideoRealtimeSummaryData(BaseModel):
    frame_count: int
    total_frames: int
    avg_fps: float
    realtime_fps: float
    inference_time: float
    model_name: str
    input_size: list[int]


class SegmentVideoFinalizeTriggerData(BaseModel):
    task_id: str
    realtime_status: str
    finalize_status: str
    message: str | None = None


class SegmentVideoResultData(BaseModel):
    task_id: str
    realtime_status: str
    finalize_status: str
    summary: SegmentVideoRealtimeSummaryData | None = None
    result: SegmentVideoData | None = None
    message: str | None = None


class SegmentResolutionOption(BaseModel):
    key: str
    input_size: list[int]
    label: str


class SegmentResolutionOptionsData(BaseModel):
    image_resolutions: list[SegmentResolutionOption]
    video_resolutions: list[SegmentResolutionOption]
    default_resolution: str
