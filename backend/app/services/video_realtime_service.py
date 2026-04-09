from __future__ import annotations

import asyncio
import base64
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path
from threading import Lock, Thread
from typing import Any

import cv2

from app.core.exceptions import AppException
from app.core.logger import logger
from app.schemas.segment import SegmentVideoData, SegmentVideoRealtimeSummaryData
from app.services.history_service import inference_history_service
from app.services.inference_service import inference_service
from app.services.model_registry import ModelConfig


@dataclass
class VideoRealtimeTask:
    task_id: str
    user_id: int
    model: ModelConfig
    input_size: tuple[int, int]
    original_video_url: str
    original_video_path: Path
    segmented_filename: str
    overlay_filename: str
    segmented_video_url: str
    overlay_video_url: str
    status: str = "queued"
    error_message: str | None = None
    summary: SegmentVideoRealtimeSummaryData | None = None
    finalize_status: str = "idle"
    finalize_error_message: str | None = None
    result: SegmentVideoData | None = None
    queues: list[asyncio.Queue[dict[str, Any]]] = field(default_factory=list)


class VideoRealtimeService:
    def __init__(self) -> None:
        self._tasks: dict[str, VideoRealtimeTask] = {}
        self._lock = Lock()

    def create_task(
        self,
        user_id: int,
        model: ModelConfig,
        input_size: tuple[int, int],
        original_video_url: str,
        original_video_path: Path,
        segmented_filename: str,
        overlay_filename: str,
    ) -> VideoRealtimeTask:
        task_id = uuid.uuid4().hex
        task = VideoRealtimeTask(
            task_id=task_id,
            user_id=user_id,
            model=model,
            input_size=input_size,
            original_video_url=original_video_url,
            original_video_path=original_video_path,
            segmented_filename=segmented_filename,
            overlay_filename=overlay_filename,
            segmented_video_url=f"/static/result/{segmented_filename}",
            overlay_video_url=f"/static/result/{overlay_filename}",
        )
        with self._lock:
            self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> VideoRealtimeTask | None:
        with self._lock:
            return self._tasks.get(task_id)

    def _update_task(self, task_id: str, **updates: Any) -> VideoRealtimeTask | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            for key, value in updates.items():
                setattr(task, key, value)
            return task

    def subscribe(self, task_id: str) -> asyncio.Queue[dict[str, Any]] | None:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=64)
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            task.queues.append(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            task.queues = [q for q in task.queues if q is not queue]

    async def _broadcast(self, task_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            queues = list(task.queues)

        for queue in queues:
            if queue.full():
                try:
                    _ = queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    def _broadcast_threadsafe(
        self,
        loop: asyncio.AbstractEventLoop,
        task_id: str,
        payload: dict[str, Any],
    ) -> None:
        if loop.is_closed():
            return
        try:
            asyncio.run_coroutine_threadsafe(self._broadcast(task_id, payload), loop)
        except RuntimeError:
            return

    @staticmethod
    def _safe_update_history(task_id: str, **updates: Any) -> None:
        try:
            inference_history_service.update_task_history(task_id=task_id, **updates)
        except Exception as ex:
            logger.warning("history update failed task_id=%s error=%s", task_id, str(ex))

    def start_task(self, task_id: str, loop: asyncio.AbstractEventLoop) -> None:
        task = self.get_task(task_id)
        if task is None:
            raise AppException("任务不存在", status_code=HTTPStatus.BAD_REQUEST)

        thread = Thread(target=self._run_task_sync, args=(task_id, loop), daemon=True)
        thread.start()

    def start_finalize_task(self, task_id: str, loop: asyncio.AbstractEventLoop) -> VideoRealtimeTask:
        task = self.get_task(task_id)
        if task is None:
            raise AppException("任务不存在", status_code=HTTPStatus.NOT_FOUND)

        if task.status != "completed":
            raise AppException(
                "实时预览任务尚未完成，暂不可生成最终视频",
                status_code=HTTPStatus.CONFLICT,
            )

        if task.finalize_status in {"queued", "running", "completed"}:
            return task

        task = self._update_task(
            task_id,
            finalize_status="queued",
            finalize_error_message=None,
        )
        if task is None:
            raise AppException("任务不存在", status_code=HTTPStatus.NOT_FOUND)

        self._safe_update_history(task_id, finalize_status="queued", status_message=None)

        thread = Thread(target=self._run_finalize_sync, args=(task_id, loop), daemon=True)
        thread.start()
        return task

    def _run_task_sync(self, task_id: str, loop: asyncio.AbstractEventLoop) -> None:
        task = self._update_task(task_id, status="running", error_message=None, summary=None)
        if task is None:
            return

        self._safe_update_history(task_id, realtime_status="running", status_message=None)

        try:
            session, input_name = inference_service._session_manager.get(task.model)
            effective_input_size = inference_service._normalize_requested_input_size(
                session, task.input_size
            )
            if effective_input_size != task.input_size:
                task = self._update_task(task_id, input_size=effective_input_size) or task
                self._safe_update_history(
                    task_id,
                    resolution=f"{effective_input_size[0]}x{effective_input_size[1]}",
                )

            self._broadcast_threadsafe(
                loop,
                task_id,
                {
                    "type": "task_started",
                    "task_id": task_id,
                    "status": task.status,
                    "model_name": task.model.model_name,
                    "input_size": [effective_input_size[0], effective_input_size[1]],
                    "original_video_url": task.original_video_url,
                    "finalize_status": task.finalize_status,
                },
            )

            capture = cv2.VideoCapture(str(task.original_video_path))
            if not capture.isOpened():
                raise AppException("读取视频失败", status_code=HTTPStatus.BAD_REQUEST)

            src_fps = capture.get(cv2.CAP_PROP_FPS)
            if src_fps <= 0:
                src_fps = 25.0

            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

            if width <= 0 or height <= 0:
                capture.release()
                raise AppException("视频尺寸无效", status_code=HTTPStatus.BAD_REQUEST)

            frame_count = 0
            inference_times: list[float] = []
            fps_window: deque[float] = deque(maxlen=30)
            realtime_fps = 0.0
            total_start = time.perf_counter()

            try:
                while True:
                    ret, frame = capture.read()
                    if not ret:
                        break

                    frame_count += 1
                    frame_start = time.perf_counter()

                    input_tensor = inference_service._preprocess(frame, effective_input_size)
                    mask, inference_time = inference_service._infer_mask(
                        session, input_name, input_tensor, effective_input_size
                    )
                    inference_times.append(inference_time)

                    restored_mask = inference_service._restore_mask_to_size(
                        mask,
                        (height, width),
                    )
                    color_mask = inference_service._mask_to_color(restored_mask)
                    overlay = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)

                    frame_elapsed = time.perf_counter() - frame_start
                    if frame_elapsed > 0:
                        fps_window.append(1.0 / frame_elapsed)
                        realtime_fps = float(sum(fps_window) / len(fps_window))

                    if frame_count % 2 == 0 or frame_count == 1:
                        progress = 0.0
                        if total_frames > 0:
                            progress = round(frame_count / total_frames * 100, 2)

                        preview = cv2.resize(overlay, (640, 360), interpolation=cv2.INTER_LINEAR)
                        ok, encoded = cv2.imencode(
                            ".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), 75]
                        )
                        preview_base64 = ""
                        if ok:
                            preview_base64 = base64.b64encode(encoded.tobytes()).decode("ascii")

                        self._broadcast_threadsafe(
                            loop,
                            task_id,
                            {
                                "type": "task_progress",
                                "task_id": task_id,
                                "status": task.status,
                                "frame_index": frame_count,
                                "total_frames": total_frames,
                                "progress": progress,
                                "realtime_fps": round(realtime_fps, 2),
                                "inference_time": round(float(inference_time), 4),
                                "preview_jpeg_base64": preview_base64,
                                "finalize_status": task.finalize_status,
                            },
                        )
            finally:
                capture.release()

            if frame_count == 0:
                raise AppException("视频中没有可处理的帧", status_code=HTTPStatus.BAD_REQUEST)

            total_elapsed = time.perf_counter() - total_start
            avg_fps = frame_count / total_elapsed if total_elapsed > 0 else 0.0
            avg_inference_time = (
                float(sum(inference_times) / len(inference_times)) if inference_times else 0.0
            )

            summary = SegmentVideoRealtimeSummaryData(
                frame_count=frame_count,
                total_frames=total_frames,
                avg_fps=round(avg_fps, 1),
                realtime_fps=round(realtime_fps or avg_fps, 1),
                inference_time=round(avg_inference_time, 3),
                model_name=task.model.model_name,
                input_size=[task.input_size[0], task.input_size[1]],
            )

            task = self._update_task(task_id, status="completed", summary=summary)
            if task is None:
                return

            self._safe_update_history(
                task_id,
                realtime_status="completed",
                finalize_status=task.finalize_status,
                avg_fps=float(summary.avg_fps),
                realtime_fps=float(summary.realtime_fps),
                inference_time=float(summary.inference_time),
                status_message=None,
            )

            self._broadcast_threadsafe(
                loop,
                task_id,
                {
                    "type": "task_completed",
                    "task_id": task_id,
                    "status": task.status,
                    "summary": summary.model_dump(),
                    "finalize_status": task.finalize_status,
                },
            )
        except Exception as ex:
            task = self._update_task(task_id, status="failed", error_message=str(ex))
            logger.error("实时视频任务失败 task_id=%s error=%s", task_id, str(ex))
            self._safe_update_history(
                task_id,
                realtime_status="failed",
                status_message=str(ex),
            )
            self._broadcast_threadsafe(
                loop,
                task_id,
                {
                    "type": "task_failed",
                    "task_id": task_id,
                    "status": task.status if task else "failed",
                    "message": str(ex),
                },
            )

    def _run_finalize_sync(self, task_id: str, loop: asyncio.AbstractEventLoop) -> None:
        task = self._update_task(
            task_id,
            finalize_status="running",
            finalize_error_message=None,
        )
        if task is None:
            return

        self._safe_update_history(task_id, finalize_status="running", status_message=None)

        self._broadcast_threadsafe(
            loop,
            task_id,
            {
                "type": "task_finalize_started",
                "task_id": task_id,
                "status": task.status,
                "finalize_status": task.finalize_status,
            },
        )

        try:
            result = inference_service.segment_video(
                original_video_url=task.original_video_url,
                original_video_path=task.original_video_path,
                model=task.model,
                segmented_filename=task.segmented_filename,
                overlay_filename=task.overlay_filename,
                input_size=task.input_size,
            )

            task = self._update_task(
                task_id,
                finalize_status="completed",
                result=result,
                finalize_error_message=None,
            )
            if task is None:
                return

            logger.info(
                "realtime finalize completed task_id=%s overlay=%s avg_fps=%s realtime_fps=%s",
                task_id,
                task.result.overlay_video_url if task.result else "",
                task.result.avg_fps if task.result else 0.0,
                task.result.realtime_fps if task.result else 0.0,
            )

            self._safe_update_history(
                task_id,
                finalize_status="completed",
                segmented_url=task.result.segmented_video_url if task.result else None,
                overlay_url=task.result.overlay_video_url if task.result else None,
                avg_fps=float(task.result.avg_fps) if task.result else None,
                realtime_fps=float(task.result.realtime_fps) if task.result else None,
                inference_time=float(task.result.inference_time) if task.result else None,
                status_message=None,
            )

            self._broadcast_threadsafe(
                loop,
                task_id,
                {
                    "type": "task_finalize_completed",
                    "task_id": task_id,
                    "status": task.status,
                    "finalize_status": task.finalize_status,
                    "result": task.result.model_dump() if task.result else None,
                },
            )
        except Exception as ex:
            task = self._update_task(
                task_id,
                finalize_status="failed",
                finalize_error_message=str(ex),
            )
            logger.error("实时任务最终视频生成失败 task_id=%s error=%s", task_id, str(ex))
            self._safe_update_history(
                task_id,
                finalize_status="failed",
                status_message=str(ex),
            )
            self._broadcast_threadsafe(
                loop,
                task_id,
                {
                    "type": "task_finalize_failed",
                    "task_id": task_id,
                    "status": task.status if task else "completed",
                    "finalize_status": "failed",
                    "message": str(ex),
                },
            )


video_realtime_service = VideoRealtimeService()
