from __future__ import annotations

import os
import time
from collections import deque
from http import HTTPStatus
from numbers import Integral
from pathlib import Path
from threading import Lock

import cv2
import numpy as np
import onnxruntime as ort

from app.core.config import RESULT_DIR
from app.core.exceptions import AppException
from app.core.logger import logger
from app.schemas.segment import SegmentClassItem, SegmentImageData, SegmentVideoData
from app.services.model_registry import ModelConfig
from app.utils.video_utils import finalize_video_for_web

CITYSCAPES_CLASS_NAMES: list[str] = [
    "road",
    "sidewalk",
    "building",
    "wall",
    "fence",
    "pole",
    "traffic light",
    "traffic sign",
    "vegetation",
    "terrain",
    "sky",
    "person",
    "rider",
    "car",
    "truck",
    "bus",
    "train",
    "motorcycle",
    "bicycle",
]

CITYSCAPES_PALETTE = np.array(
    [
        [128, 64, 128],
        [244, 35, 232],
        [70, 70, 70],
        [102, 102, 156],
        [190, 153, 153],
        [153, 153, 153],
        [250, 170, 30],
        [220, 220, 0],
        [107, 142, 35],
        [152, 251, 152],
        [70, 130, 180],
        [220, 20, 60],
        [255, 0, 0],
        [0, 0, 142],
        [0, 0, 70],
        [0, 60, 100],
        [0, 80, 100],
        [0, 0, 230],
        [119, 11, 32],
    ],
    dtype=np.uint8,
)

MEAN = np.array([123.675, 116.28, 103.53], dtype=np.float32)
STD = np.array([58.395, 57.12, 57.375], dtype=np.float32)


class ONNXSessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, ort.InferenceSession] = {}
        self._input_names: dict[str, str] = {}
        self._lock = Lock()

    @staticmethod
    def _add_dll_search_path(path: Path) -> None:
        if not path.exists() or not path.is_dir():
            return
        path_str = str(path.resolve())
        if path_str not in os.environ.get("PATH", ""):
            os.environ["PATH"] = path_str + ";" + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(path_str)
            except OSError:
                pass

    @classmethod
    def _ensure_runtime_paths(cls) -> None:
        project_root = Path(__file__).resolve().parents[2]
        runtime_dll_dir = project_root / "runtime_dlls"
        ort_capi_dir = Path(ort.__file__).resolve().parent / "capi"

        # Strategy 1 (default): load custom runtime DLLs from project runtime_dlls
        cls._add_dll_search_path(runtime_dll_dir)

        # Strategy 2 (optional): inject CUDA bin via environment variable
        cuda_bin_path_env = os.getenv("CUDA_BIN_PATH", "")
        if cuda_bin_path_env:
            cls._add_dll_search_path(Path(cuda_bin_path_env))

        # Strategy 3 (debug, keep commented): fixed CUDA path toggle
        # cuda_bin_path = Path(r"D:\CUDA\v12.4\bin")
        # cls._add_dll_search_path(cuda_bin_path)

        # Also add ONNX Runtime capi directory to avoid shared provider missing
        cls._add_dll_search_path(ort_capi_dir)

    def get(self, model: ModelConfig) -> tuple[ort.InferenceSession, str]:
        with self._lock:
            if model.model_key in self._sessions:
                return self._sessions[model.model_key], self._input_names[model.model_key]

            if not model.model_path.exists():
                raise AppException(
                    message=f"模型文件不存在: {model.model_path}",
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                )

            self._ensure_runtime_paths()

            providers: list[ort.ProviderType]
            providers = [
                (
                    "CUDAExecutionProvider",
                    {
                        "device_id": 0,
                        "arena_extend_strategy": "kNextPowerOfTwo",
                        "cudnn_conv_algo_search": "EXHAUSTIVE",
                        "do_copy_in_default_stream": True,
                    },
                ),
                "CPUExecutionProvider",
            ]

            try:
                session = ort.InferenceSession(str(model.model_path), providers=providers)
            except Exception as ex:
                logger.warning(
                    "模型 %s CUDA 初始化失败，回退 CPU。error=%s",
                    model.model_key,
                    str(ex),
                )
                session = ort.InferenceSession(
                    str(model.model_path), providers=["CPUExecutionProvider"]
                )

            input_name = session.get_inputs()[0].name
            self._sessions[model.model_key] = session
            self._input_names[model.model_key] = input_name
            logger.info(
                "模型已加载 model_key=%s providers=%s path=%s",
                model.model_key,
                session.get_providers(),
                str(model.model_path),
            )
            return session, input_name


class InferenceService:
    def __init__(self) -> None:
        self._session_manager = ONNXSessionManager()

    @staticmethod
    def _normalize_requested_input_size(
        session: ort.InferenceSession,
        requested_size: tuple[int, int],
    ) -> tuple[int, int]:
        normalized_h, normalized_w = int(requested_size[0]), int(requested_size[1])
        input_shape = session.get_inputs()[0].shape

        if len(input_shape) >= 4:
            h_dim = input_shape[2]
            w_dim = input_shape[3]

            if isinstance(h_dim, Integral) and int(h_dim) > 0:
                normalized_h = int(h_dim)
            if isinstance(w_dim, Integral) and int(w_dim) > 0:
                normalized_w = int(w_dim)

        return normalized_h, normalized_w

    @staticmethod
    def _restore_mask_to_size(
        mask_input: np.ndarray,
        target_size: tuple[int, int],
    ) -> np.ndarray:
        target_h, target_w = int(target_size[0]), int(target_size[1])
        if mask_input.shape[0] == target_h and mask_input.shape[1] == target_w:
            return mask_input
        return cv2.resize(mask_input, (target_w, target_h), interpolation=cv2.INTER_NEAREST)

    @staticmethod
    def _preprocess(frame_bgr: np.ndarray, input_size: tuple[int, int]) -> np.ndarray:
        input_h, input_w = input_size
        img = cv2.resize(frame_bgr, (input_w, input_h), interpolation=cv2.INTER_LINEAR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = (img.astype(np.float32) - MEAN) / STD
        img = img.transpose(2, 0, 1)
        return np.expand_dims(img, axis=0).astype(np.float32)

    @staticmethod
    def _infer_mask(
        session: ort.InferenceSession,
        input_name: str,
        input_tensor: np.ndarray,
        input_size: tuple[int, int],
    ) -> tuple[np.ndarray, float]:
        t0 = time.perf_counter()
        outputs = session.run(None, {input_name: input_tensor})
        inference_time = time.perf_counter() - t0

        logits = outputs[0]
        mask = np.argmax(logits, axis=1).squeeze().astype(np.uint8)

        input_h, input_w = input_size
        if mask.ndim != 2:
            raise AppException(
                message="模型输出异常，mask 维度不正确",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        if mask.shape[0] != input_h or mask.shape[1] != input_w:
            mask = cv2.resize(mask, (input_w, input_h), interpolation=cv2.INTER_NEAREST)

        return mask, inference_time

    @staticmethod
    def _mask_to_color(mask: np.ndarray) -> np.ndarray:
        clipped = np.clip(mask, 0, len(CITYSCAPES_PALETTE) - 1)
        color_rgb = CITYSCAPES_PALETTE[clipped]
        return cv2.cvtColor(color_rgb, cv2.COLOR_RGB2BGR)

    @staticmethod
    def _build_display_color_mask(
        mask: np.ndarray,
        target_size: tuple[int, int],
        mode: str,
    ) -> np.ndarray:
        normalized_mode = str(mode).strip().lower()
        if normalized_mode == "quality":
            restored_mask = InferenceService._restore_mask_to_size(mask, target_size)
            return InferenceService._mask_to_color(restored_mask)

        color_mask_input = InferenceService._mask_to_color(mask)
        return InferenceService._restore_mask_to_size(color_mask_input, target_size)

    @staticmethod
    def _mask_to_classes(mask: np.ndarray) -> list[SegmentClassItem]:
        total_pixels = mask.size
        if total_pixels <= 0:
            return []

        values, counts = np.unique(mask, return_counts=True)
        class_items: list[SegmentClassItem] = []

        for class_id, count in sorted(
            zip(values.tolist(), counts.tolist()), key=lambda x: x[1], reverse=True
        ):
            if class_id < 0 or class_id >= len(CITYSCAPES_CLASS_NAMES):
                continue
            ratio = round(float(count / total_pixels * 100), 2)
            if ratio < 0.1:
                continue
            rgb = CITYSCAPES_PALETTE[class_id]
            color_hex = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            class_items.append(
                SegmentClassItem(
                    name=CITYSCAPES_CLASS_NAMES[class_id],
                    color=color_hex,
                    ratio=ratio,
                )
            )

        return class_items[:10]

    def segment_image(
        self,
        original_image_url: str,
        original_image_path: Path,
        model: ModelConfig,
        segmented_filename: str,
        overlay_filename: str,
        input_size: tuple[int, int] | None = None,
    ) -> SegmentImageData:
        frame = cv2.imread(str(original_image_path), cv2.IMREAD_COLOR)
        if frame is None:
            raise AppException("读取图片失败", status_code=HTTPStatus.BAD_REQUEST)

        session, input_name = self._session_manager.get(model)
        requested_input_size = input_size or model.input_size
        effective_input_size = self._normalize_requested_input_size(
            session, requested_input_size
        )

        input_tensor = self._preprocess(frame, effective_input_size)
        mask, inference_time = self._infer_mask(
            session, input_name, input_tensor, effective_input_size
        )
        original_size = (frame.shape[0], frame.shape[1])
        restored_mask = self._restore_mask_to_size(mask, original_size)

        color_mask = self._mask_to_color(restored_mask)
        overlay = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)

        segmented_path = RESULT_DIR / segmented_filename
        overlay_path = RESULT_DIR / overlay_filename
        if not cv2.imwrite(str(segmented_path), color_mask):
            raise AppException("写入分割结果图片失败", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
        if not cv2.imwrite(str(overlay_path), overlay):
            raise AppException("写入融合结果图片失败", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

        classes = self._mask_to_classes(restored_mask)

        return SegmentImageData(
            original_image_url=original_image_url,
            segmented_image_url=f"/static/result/{segmented_filename}",
            overlay_image_url=f"/static/result/{overlay_filename}",
            inference_time=round(float(inference_time), 3),
            model_name=model.model_name,
            input_size=[effective_input_size[0], effective_input_size[1]],
            classes=classes,
        )

    def segment_video(
        self,
        original_video_url: str,
        original_video_path: Path,
        model: ModelConfig,
        segmented_filename: str,
        overlay_filename: str,
        input_size: tuple[int, int] | None = None,
    ) -> SegmentVideoData:
        session, input_name = self._session_manager.get(model)
        requested_input_size = input_size or model.input_size
        effective_input_size = self._normalize_requested_input_size(
            session, requested_input_size
        )

        capture = cv2.VideoCapture(str(original_video_path))
        if not capture.isOpened():
            raise AppException("读取视频失败", status_code=HTTPStatus.BAD_REQUEST)

        src_fps = capture.get(cv2.CAP_PROP_FPS)
        if src_fps <= 0:
            src_fps = 25.0

        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            capture.release()
            raise AppException("视频尺寸无效", status_code=HTTPStatus.BAD_REQUEST)

        segmented_path = RESULT_DIR / segmented_filename
        overlay_path = RESULT_DIR / overlay_filename

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        segmented_writer = cv2.VideoWriter(str(segmented_path), fourcc, src_fps, (width, height))
        overlay_writer = cv2.VideoWriter(str(overlay_path), fourcc, src_fps, (width, height))

        if not segmented_writer.isOpened() or not overlay_writer.isOpened():
            capture.release()
            segmented_writer.release()
            overlay_writer.release()
            raise AppException("创建结果视频失败，请检查编码器", status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

        frame_count = 0
        inference_times: list[float] = []
        fps_window: deque[float] = deque(maxlen=30)
        realtime_fps = 0.0
        total_start = time.perf_counter()
        postprocess_mode = "quality"

        try:
            while True:
                ret, frame = capture.read()
                if not ret:
                    break

                frame_count += 1
                frame_start = time.perf_counter()

                input_tensor = self._preprocess(frame, effective_input_size)
                mask, inference_time = self._infer_mask(
                    session, input_name, input_tensor, effective_input_size
                )
                inference_times.append(inference_time)

                color_mask = self._build_display_color_mask(
                    mask=mask,
                    target_size=(height, width),
                    mode=postprocess_mode,
                )
                overlay = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)

                segmented_writer.write(color_mask)
                overlay_writer.write(overlay)

                frame_elapsed = time.perf_counter() - frame_start
                if frame_elapsed > 0:
                    fps_window.append(1.0 / frame_elapsed)
                    realtime_fps = float(sum(fps_window) / len(fps_window))
        finally:
            capture.release()
            segmented_writer.release()
            overlay_writer.release()

        if frame_count == 0:
            raise AppException("视频中没有可处理的帧", status_code=HTTPStatus.BAD_REQUEST)

        logger.info(
            "=== BEFORE FINALIZE sync segmented=%s size=%s overlay=%s size=%s",
            str(segmented_path),
            segmented_path.stat().st_size if segmented_path.exists() else -1,
            str(overlay_path),
            overlay_path.stat().st_size if overlay_path.exists() else -1,
        )
        segmented_meta = finalize_video_for_web(segmented_path, task_tag="sync-segmented")
        overlay_meta = finalize_video_for_web(overlay_path, task_tag="sync-overlay")
        logger.info(
            "=== AFTER FINALIZE sync segmented_codec=%s overlay_codec=%s segmented_duration=%s overlay_duration=%s",
            segmented_meta.get("codec"),
            overlay_meta.get("codec"),
            segmented_meta.get("duration"),
            overlay_meta.get("duration"),
        )

        total_elapsed = time.perf_counter() - total_start
        avg_fps = frame_count / total_elapsed if total_elapsed > 0 else 0.0
        avg_inference_time = (
            float(sum(inference_times) / len(inference_times)) if inference_times else 0.0
        )

        logger.info(
            "sync video finalized segmented=%s overlay=%s input_size=%s postprocess_mode=%s",
            segmented_meta,
            overlay_meta,
            effective_input_size,
            postprocess_mode,
        )

        return SegmentVideoData(
            original_video_url=original_video_url,
            segmented_video_url=f"/static/result/{segmented_filename}",
            overlay_video_url=f"/static/result/{overlay_filename}",
            avg_fps=round(avg_fps, 1),
            realtime_fps=round(realtime_fps or avg_fps, 1),
            inference_time=round(avg_inference_time, 3),
            model_name=model.model_name,
            input_size=[effective_input_size[0], effective_input_size[1]],
        )
inference_service = InferenceService()





