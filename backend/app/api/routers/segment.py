from __future__ import annotations

import asyncio
import time
from http import HTTPStatus

from fastapi import APIRouter, File, Form, Request, UploadFile, WebSocket, WebSocketDisconnect

from app.core.config import UPLOAD_DIR, settings
from app.core.exceptions import AppException
from app.core.logger import logger
from app.core.responses import success_response
from app.schemas.common import ApiResponse
from app.schemas.segment import (
    SegmentImageData,
    SegmentResolutionOptionsData,
    SegmentVideoData,
    SegmentVideoFinalizeTriggerData,
    SegmentVideoRealtimeInitData,
    SegmentVideoResultData,
)
from app.services.inference_service import inference_service
from app.services.model_registry import get_model_config
from app.services.resolution_service import (
    DEFAULT_RESOLUTION_KEY,
    list_resolution_options,
    parse_resolution_or_default,
)
from app.services.video_realtime_service import video_realtime_service
from app.utils.file_utils import build_unique_filename, save_upload_file, validate_upload_file

router = APIRouter(prefix="/segment", tags=["segment"])


@router.get("/resolutions", response_model=ApiResponse[SegmentResolutionOptionsData])
async def get_segment_resolutions() -> ApiResponse[SegmentResolutionOptionsData]:
    options = list_resolution_options()
    data = SegmentResolutionOptionsData(
        image_resolutions=options,
        video_resolutions=options,
        default_resolution=DEFAULT_RESOLUTION_KEY,
    )
    return success_response(data)


@router.post("", response_model=ApiResponse[SegmentImageData])
async def segment_image(
    request: Request,
    file: UploadFile = File(...),
    model_key: str = Form(default=settings.default_model_key),
    resolution: str | None = Form(default=None),
) -> ApiResponse[SegmentImageData]:
    request_id = getattr(request.state, "request_id", "-")
    t0 = time.perf_counter()

    if not file.filename:
        raise AppException("缺少文件名", status_code=HTTPStatus.BAD_REQUEST)

    validate_upload_file(file, "image")
    model = get_model_config(model_key)
    selected_input_size = parse_resolution_or_default(resolution, model.input_size)

    upload_filename = build_unique_filename(file.filename)
    upload_path = UPLOAD_DIR / upload_filename
    await save_upload_file(file, upload_path)

    segmented_filename = f"{upload_path.stem}_mask.png"
    overlay_filename = f"{upload_path.stem}_overlay.png"

    original_url = f"{settings.static_url_prefix}/upload/{upload_filename}"
    result = inference_service.segment_image(
        original_image_url=original_url,
        original_image_path=upload_path,
        model=model,
        segmented_filename=segmented_filename,
        overlay_filename=overlay_filename,
        input_size=selected_input_size,
    )

    logger.info(
        "request_id=%s endpoint=/api/segment model=%s resolution=%s file=%s elapsed=%.3fs",
        request_id,
        model_key,
        f"{selected_input_size[0]}x{selected_input_size[1]}",
        upload_filename,
        time.perf_counter() - t0,
    )
    return success_response(result)


@router.post("/video", response_model=ApiResponse[SegmentVideoData])
async def segment_video(
    request: Request,
    file: UploadFile = File(...),
    model_key: str = Form(default=settings.default_model_key),
    resolution: str | None = Form(default=None),
) -> ApiResponse[SegmentVideoData]:
    request_id = getattr(request.state, "request_id", "-")
    t0 = time.perf_counter()

    if not file.filename:
        raise AppException("缺少文件名", status_code=HTTPStatus.BAD_REQUEST)

    validate_upload_file(file, "video")
    model = get_model_config(model_key)
    selected_input_size = parse_resolution_or_default(resolution, model.input_size)

    upload_filename = build_unique_filename(file.filename)
    upload_path = UPLOAD_DIR / upload_filename
    await save_upload_file(file, upload_path)

    segmented_filename = f"{upload_path.stem}_mask.mp4"
    overlay_filename = f"{upload_path.stem}_overlay.mp4"

    original_url = f"{settings.static_url_prefix}/upload/{upload_filename}"
    result = inference_service.segment_video(
        original_video_url=original_url,
        original_video_path=upload_path,
        model=model,
        segmented_filename=segmented_filename,
        overlay_filename=overlay_filename,
        input_size=selected_input_size,
    )

    logger.info(
        "request_id=%s endpoint=/api/segment/video model=%s resolution=%s file=%s elapsed=%.3fs",
        request_id,
        model_key,
        f"{selected_input_size[0]}x{selected_input_size[1]}",
        upload_filename,
        time.perf_counter() - t0,
    )
    return success_response(result)


@router.post("/video/realtime", response_model=ApiResponse[SegmentVideoRealtimeInitData])
async def start_video_realtime(
    request: Request,
    file: UploadFile = File(...),
    model_key: str = Form(default=settings.default_model_key),
    resolution: str | None = Form(default=None),
) -> ApiResponse[SegmentVideoRealtimeInitData]:
    request_id = getattr(request.state, "request_id", "-")
    t0 = time.perf_counter()

    if not file.filename:
        raise AppException("缺少文件名", status_code=HTTPStatus.BAD_REQUEST)

    validate_upload_file(file, "video")
    model = get_model_config(model_key)
    selected_input_size = parse_resolution_or_default(resolution, model.input_size)

    upload_filename = build_unique_filename(file.filename)
    upload_path = UPLOAD_DIR / upload_filename
    await save_upload_file(file, upload_path)

    segmented_filename = f"{upload_path.stem}_mask.mp4"
    overlay_filename = f"{upload_path.stem}_overlay.mp4"

    original_url = f"{settings.static_url_prefix}/upload/{upload_filename}"
    task = video_realtime_service.create_task(
        model=model,
        input_size=selected_input_size,
        original_video_url=original_url,
        original_video_path=upload_path,
        segmented_filename=segmented_filename,
        overlay_filename=overlay_filename,
    )

    event_loop = asyncio.get_running_loop()
    video_realtime_service.start_task(task.task_id, event_loop)

    data = SegmentVideoRealtimeInitData(
        task_id=task.task_id,
        ws_url=f"/api/segment/video/ws/{task.task_id}",
        status=task.status,
        finalize_status=task.finalize_status,
        original_video_url=task.original_video_url,
        segmented_video_url=task.segmented_video_url,
        overlay_video_url=task.overlay_video_url,
        model_name=model.model_name,
        input_size=[selected_input_size[0], selected_input_size[1]],
    )

    logger.info(
        "request_id=%s endpoint=/api/segment/video/realtime model=%s resolution=%s file=%s task_id=%s elapsed=%.3fs",
        request_id,
        model_key,
        f"{selected_input_size[0]}x{selected_input_size[1]}",
        upload_filename,
        task.task_id,
        time.perf_counter() - t0,
    )
    return success_response(data)


@router.post("/video/finalize/{task_id}", response_model=ApiResponse[SegmentVideoFinalizeTriggerData])
async def start_video_finalize(request: Request, task_id: str) -> ApiResponse[SegmentVideoFinalizeTriggerData]:
    request_id = getattr(request.state, "request_id", "-")
    t0 = time.perf_counter()

    event_loop = asyncio.get_running_loop()
    task = video_realtime_service.start_finalize_task(task_id, event_loop)

    message = "已触发最终视频生成"
    if task.finalize_status == "running":
        message = "最终视频生成中"
    elif task.finalize_status == "completed":
        message = "最终视频已可用"

    data = SegmentVideoFinalizeTriggerData(
        task_id=task.task_id,
        realtime_status=task.status,
        finalize_status=task.finalize_status,
        message=message,
    )

    logger.info(
        "request_id=%s endpoint=/api/segment/video/finalize task_id=%s realtime_status=%s finalize_status=%s elapsed=%.3fs",
        request_id,
        task_id,
        task.status,
        task.finalize_status,
        time.perf_counter() - t0,
    )
    return success_response(data)


@router.get("/video/result/{task_id}", response_model=ApiResponse[SegmentVideoResultData])
async def get_video_result(request: Request, task_id: str) -> ApiResponse[SegmentVideoResultData]:
    request_id = getattr(request.state, "request_id", "-")
    t0 = time.perf_counter()

    task = video_realtime_service.get_task(task_id)
    if task is None:
        raise AppException("任务不存在", status_code=HTTPStatus.NOT_FOUND)

    message = task.error_message
    if task.finalize_status == "failed":
        message = task.finalize_error_message

    data = SegmentVideoResultData(
        task_id=task.task_id,
        realtime_status=task.status,
        finalize_status=task.finalize_status,
        summary=task.summary,
        result=task.result,
        message=message,
    )

    logger.info(
        "request_id=%s endpoint=/api/segment/video/result task_id=%s realtime_status=%s finalize_status=%s elapsed=%.3fs",
        request_id,
        task_id,
        task.status,
        task.finalize_status,
        time.perf_counter() - t0,
    )
    return success_response(data)


@router.websocket("/video/ws/{task_id}")
async def video_realtime_ws(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()

    queue = video_realtime_service.subscribe(task_id)
    if queue is None:
        await websocket.send_json(
            {
                "type": "task_failed",
                "task_id": task_id,
                "status": "failed",
                "message": "任务不存在",
            }
        )
        await websocket.close(code=1008)
        return

    task = video_realtime_service.get_task(task_id)
    if task is not None:
        await websocket.send_json(
            {
                "type": "task_snapshot",
                "task_id": task.task_id,
                "status": task.status,
                "finalize_status": task.finalize_status,
                "summary": task.summary.model_dump() if task.summary else None,
                "result": task.result.model_dump() if task.result else None,
                "message": task.error_message or task.finalize_error_message,
            }
        )
        if task.status in {"completed", "failed"}:
            await websocket.close(code=1000)
            video_realtime_service.unsubscribe(task_id, queue)
            return

    try:
        while True:
            payload = await queue.get()
            await websocket.send_json(payload)
            if payload.get("type") in {"task_completed", "task_failed"}:
                break
    except WebSocketDisconnect:
        logger.info("websocket disconnected task_id=%s", task_id)
    finally:
        video_realtime_service.unsubscribe(task_id, queue)
        try:
            await websocket.close(code=1000)
        except RuntimeError:
            pass
