from __future__ import annotations

import argparse
import base64
import sys
import time
from pathlib import Path

import cv2

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.inference_service import inference_service
from app.services.model_registry import get_model_config


def parse_resolution(text: str) -> tuple[int, int]:
    if "x" not in text:
        raise ValueError("resolution format must be HxW, e.g. 256x512")
    h_str, w_str = text.lower().split("x", 1)
    h = int(h_str)
    w = int(w_str)
    if h <= 0 or w <= 0:
        raise ValueError("resolution values must be positive")
    return h, w


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile realtime-like pipeline on a chosen input resolution."
    )
    parser.add_argument("--video", default="test/assets/test-1-short.mp4")
    parser.add_argument("--model-key", default="bisenetv2")
    parser.add_argument("--resolution", default="256x512")
    parser.add_argument("--frames", type=int, default=90)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--disable-write", action="store_true")
    parser.add_argument("--disable-preview", action="store_true")
    args = parser.parse_args()

    video = Path(args.video)
    if not video.exists():
        raise FileNotFoundError(f"video not found: {video}")

    input_size = parse_resolution(args.resolution)

    model = get_model_config(args.model_key)
    session, input_name = inference_service._session_manager.get(model)

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"failed to open video: {video}")

    src_fps = float(cap.get(cv2.CAP_PROP_FPS))
    if src_fps <= 0:
        src_fps = 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width <= 0 or height <= 0:
        cap.release()
        raise RuntimeError("invalid video dimensions")

    out_mask = Path("test/output/_diag_mask.mp4")
    out_overlay = Path("test/output/_diag_overlay.mp4")
    out_mask.parent.mkdir(parents=True, exist_ok=True)

    writer_mask = None
    writer_overlay = None
    if not args.disable_write:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer_mask = cv2.VideoWriter(str(out_mask), fourcc, src_fps, (width, height))
        writer_overlay = cv2.VideoWriter(str(out_overlay), fourcc, src_fps, (width, height))
        if not writer_mask.isOpened() or not writer_overlay.isOpened():
            cap.release()
            writer_mask.release()
            writer_overlay.release()
            raise RuntimeError("failed to open writers")

    # warmup
    ok, first = cap.read()
    if not ok:
        cap.release()
        if writer_mask:
            writer_mask.release()
            writer_overlay.release()
        raise RuntimeError("no frames for warmup")
    warmup_tensor = inference_service._preprocess(first, input_size)
    for _ in range(max(0, args.warmup)):
        _ = session.run(None, {input_name: warmup_tensor})
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    stats = {"read": 0.0, "pre": 0.0, "infer": 0.0, "post": 0.0, "write": 0.0, "preview": 0.0}

    processed = 0
    t0 = time.perf_counter()

    try:
        while processed < max(1, args.frames):
            t = time.perf_counter()
            ok, frame = cap.read()
            stats["read"] += time.perf_counter() - t
            if not ok:
                break

            processed += 1

            t = time.perf_counter()
            input_tensor = inference_service._preprocess(frame, input_size)
            stats["pre"] += time.perf_counter() - t

            t = time.perf_counter()
            mask, _ = inference_service._infer_mask(session, input_name, input_tensor, input_size)
            stats["infer"] += time.perf_counter() - t

            t = time.perf_counter()
            color_mask_input = inference_service._mask_to_color(mask)
            color_mask = cv2.resize(color_mask_input, (width, height), interpolation=cv2.INTER_NEAREST)
            overlay = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)
            stats["post"] += time.perf_counter() - t

            if writer_mask is not None and writer_overlay is not None:
                t = time.perf_counter()
                writer_mask.write(color_mask)
                writer_overlay.write(overlay)
                stats["write"] += time.perf_counter() - t

            if not args.disable_preview and (processed == 1 or processed % 3 == 0):
                t = time.perf_counter()
                preview = cv2.resize(overlay, (640, 360), interpolation=cv2.INTER_LINEAR)
                ok_jpg, encoded = cv2.imencode(".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                if ok_jpg:
                    _ = base64.b64encode(encoded.tobytes()).decode("ascii")
                stats["preview"] += time.perf_counter() - t
    finally:
        cap.release()
        if writer_mask is not None:
            writer_mask.release()
        if writer_overlay is not None:
            writer_overlay.release()

    elapsed = time.perf_counter() - t0
    fps = processed / elapsed if elapsed > 0 else 0.0

    print("=== Realtime-like Resolution Profile ===")
    print("video:", video)
    print("resolution:", f"{input_size[0]}x{input_size[1]}")
    print("frames:", processed)
    print("disable_write:", args.disable_write)
    print("disable_preview:", args.disable_preview)
    print("fps:", round(fps, 2))
    print("seconds:", round(elapsed, 3))

    print("\n--- stage seconds / pct ---")
    for k in ("read", "pre", "infer", "post", "write", "preview"):
        v = stats[k]
        pct = (v / elapsed * 100.0) if elapsed > 0 else 0.0
        print(f"{k:>7}: {v:>7.4f}s | {pct:>6.2f}%")


if __name__ == "__main__":
    main()
