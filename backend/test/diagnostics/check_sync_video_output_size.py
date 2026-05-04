from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import RESULT_DIR
from app.services.inference_service import inference_service
from app.services.model_registry import get_model_config


def parse_resolution(text: str) -> tuple[int, int]:
    if "x" not in text:
        raise ValueError("resolution must be formatted as HxW, e.g. 256x512")
    h_str, w_str = text.lower().split("x", 1)
    h = int(h_str)
    w = int(w_str)
    if h <= 0 or w <= 0:
        raise ValueError("resolution values must be positive")
    return h, w


def read_video_size(video_path: Path) -> tuple[int, int]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"failed to open video: {video_path}")
    try:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    finally:
        cap.release()
    if width <= 0 or height <= 0:
        raise RuntimeError(f"invalid video dimensions: {video_path}")
    return height, width


def resolve_result_path(url: str) -> Path:
    filename = url.rsplit("/", 1)[-1]
    return RESULT_DIR / filename


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Guard test: sync/finalize output video size must match input size."
    )
    parser.add_argument("--video", default="test/assets/test-1-short.mp4")
    parser.add_argument("--model-key", default="bisenetv2")
    parser.add_argument("--resolution", default="256x512")
    parser.add_argument("--keep-output", action="store_true")
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        raise FileNotFoundError(f"video not found: {video_path}")

    input_size = parse_resolution(args.resolution)
    model = get_model_config(args.model_key)
    stamp = int(time.time() * 1000)
    segmented_name = f"_guard_sync_mask_{stamp}.mp4"
    overlay_name = f"_guard_sync_overlay_{stamp}.mp4"

    expected_size = read_video_size(video_path)
    result = inference_service.segment_video(
        original_video_url=f"/static/upload/{video_path.name}",
        original_video_path=video_path,
        model=model,
        segmented_filename=segmented_name,
        overlay_filename=overlay_name,
        input_size=input_size,
    )

    segmented_path = resolve_result_path(result.segmented_video_url)
    overlay_path = resolve_result_path(result.overlay_video_url)

    segmented_size = read_video_size(segmented_path)
    overlay_size = read_video_size(overlay_path)

    if segmented_size != expected_size:
        raise AssertionError(
            f"segmented video size mismatch: expected={expected_size} actual={segmented_size}"
        )
    if overlay_size != expected_size:
        raise AssertionError(
            f"overlay video size mismatch: expected={expected_size} actual={overlay_size}"
        )

    print("PASS check_sync_video_output_size")
    print(f"input_video={video_path}")
    print(f"expected_size={expected_size[0]}x{expected_size[1]}")
    print(f"segmented_video={segmented_path} size={segmented_size[0]}x{segmented_size[1]}")
    print(f"overlay_video={overlay_path} size={overlay_size[0]}x{overlay_size[1]}")

    if not args.keep_output:
        for output_path in (segmented_path, overlay_path):
            if output_path.exists():
                output_path.unlink()


if __name__ == "__main__":
    main()

