from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import cv2

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.inference_service import inference_service
from app.services.model_registry import get_model_config


@dataclass
class ProfileStats:
    mode: str
    frames: int = 0
    preprocess_s: float = 0.0
    infer_s: float = 0.0
    postprocess_s: float = 0.0
    overlay_s: float = 0.0
    preview_s: float = 0.0
    total_s: float = 0.0

    @property
    def fps(self) -> float:
        if self.total_s <= 0:
            return 0.0
        return self.frames / self.total_s


def parse_resolution(text: str) -> tuple[int, int]:
    if "x" not in text:
        raise ValueError("resolution must be formatted as HxW, e.g. 256x512")
    h_str, w_str = text.lower().split("x", 1)
    h = int(h_str)
    w = int(w_str)
    if h <= 0 or w <= 0:
        raise ValueError("resolution values must be positive")
    return h, w


def profile_mode(
    video_path: Path,
    effective_size: tuple[int, int],
    session,
    input_name: str,
    mode: str,
    warmup: int,
    frames: int,
) -> ProfileStats:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"failed to open video: {video_path}")

    stats = ProfileStats(mode=mode)
    frame_index = 0

    try:
        while stats.frames < frames:
            ok, frame = cap.read()
            if not ok:
                break
            frame_index += 1

            if frame_index <= warmup:
                warmup_tensor = inference_service._preprocess(frame, effective_size)
                warmup_mask, _ = inference_service._infer_mask(
                    session,
                    input_name,
                    warmup_tensor,
                    effective_size,
                )
                _ = inference_service._build_display_color_mask(
                    warmup_mask,
                    (frame.shape[0], frame.shape[1]),
                    mode,
                )
                continue

            t_frame = time.perf_counter()

            t0 = time.perf_counter()
            input_tensor = inference_service._preprocess(frame, effective_size)
            stats.preprocess_s += time.perf_counter() - t0

            mask, infer_s = inference_service._infer_mask(
                session,
                input_name,
                input_tensor,
                effective_size,
            )
            stats.infer_s += infer_s

            t1 = time.perf_counter()
            color_mask = inference_service._build_display_color_mask(
                mask,
                (frame.shape[0], frame.shape[1]),
                mode,
            )
            stats.postprocess_s += time.perf_counter() - t1

            if color_mask.shape[0] != frame.shape[0] or color_mask.shape[1] != frame.shape[1]:
                raise AssertionError(
                    "display mask size mismatch: "
                    f"mode={mode} frame={(frame.shape[0], frame.shape[1])} "
                    f"mask={(color_mask.shape[0], color_mask.shape[1])}"
                )

            t2 = time.perf_counter()
            overlay = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)
            stats.overlay_s += time.perf_counter() - t2

            if stats.frames % 2 == 0:
                t3 = time.perf_counter()
                preview = cv2.resize(overlay, (640, 360), interpolation=cv2.INTER_LINEAR)
                _ = cv2.imencode(".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                stats.preview_s += time.perf_counter() - t3

            stats.total_s += time.perf_counter() - t_frame
            stats.frames += 1
    finally:
        cap.release()

    if stats.frames == 0:
        raise RuntimeError("no frames sampled for profiling")

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Guard test: realtime_fast should be significantly faster than quality mode, "
            "while preserving output frame size."
        )
    )
    parser.add_argument("--video", default="test/assets/test-1-short.mp4")
    parser.add_argument("--model-key", default="bisenetv2")
    parser.add_argument("--resolution", default="256x512")
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--frames", type=int, default=90)
    parser.add_argument("--min-ratio", type=float, default=1.5)
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        raise FileNotFoundError(f"video not found: {video_path}")

    input_size = parse_resolution(args.resolution)
    model = get_model_config(args.model_key)
    session, input_name = inference_service._session_manager.get(model)
    effective_size = inference_service._normalize_requested_input_size(session, input_size)

    quality_stats = profile_mode(
        video_path=video_path,
        effective_size=effective_size,
        session=session,
        input_name=input_name,
        mode="quality",
        warmup=args.warmup,
        frames=args.frames,
    )
    fast_stats = profile_mode(
        video_path=video_path,
        effective_size=effective_size,
        session=session,
        input_name=input_name,
        mode="realtime_fast",
        warmup=args.warmup,
        frames=args.frames,
    )

    ratio = fast_stats.fps / quality_stats.fps if quality_stats.fps > 0 else 0.0
    if ratio < args.min_ratio:
        raise AssertionError(
            "realtime_fast speedup check failed: "
            f"fast_fps={fast_stats.fps:.2f} quality_fps={quality_stats.fps:.2f} "
            f"ratio={ratio:.2f} expected>={args.min_ratio:.2f}"
        )

    print("PASS check_realtime_postprocess_ratio")
    print(f"video={video_path}")
    print(f"model={model.model_key} effective_size={effective_size}")
    print(
        "quality: "
        f"fps={quality_stats.fps:.2f} "
        f"post={quality_stats.postprocess_s / quality_stats.frames:.4f}s/frame"
    )
    print(
        "realtime_fast: "
        f"fps={fast_stats.fps:.2f} "
        f"post={fast_stats.postprocess_s / fast_stats.frames:.4f}s/frame"
    )
    print(f"speedup_ratio={ratio:.2f} threshold={args.min_ratio:.2f}")


if __name__ == "__main__":
    main()

