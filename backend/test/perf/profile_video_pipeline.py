from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import cv2

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import RESULT_DIR
from app.services.inference_service import inference_service
from app.services.model_registry import get_model_config
from app.utils.video_utils import finalize_video_for_web


@dataclass
class ProfileOptions:
    video: Path
    model_key: str
    frame_limit: int
    preview_every: int
    warmup_runs: int
    disable_preview: bool
    disable_write: bool
    disable_finalize: bool
    output_tag: str


def _resolve_video_path(video_arg: str) -> Path:
    candidate = Path(video_arg)
    if candidate.exists():
        return candidate
    fallback = Path("test/assets/sample_video.mp4")
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"video not found: {candidate}")


def _safe_div(a: float, b: float) -> float:
    if b <= 0:
        return 0.0
    return a / b


def run_profile(options: ProfileOptions) -> dict[str, object]:
    model = get_model_config(options.model_key)
    session, input_name = inference_service._session_manager.get(model)

    capture = cv2.VideoCapture(str(options.video))
    if not capture.isOpened():
        raise RuntimeError(f"failed to open video: {options.video}")

    src_fps = float(capture.get(cv2.CAP_PROP_FPS))
    if src_fps <= 0:
        src_fps = 25.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if width <= 0 or height <= 0:
        capture.release()
        raise RuntimeError("invalid video width/height")

    segmented_path = RESULT_DIR / f"{options.output_tag}_mask.mp4"
    overlay_path = RESULT_DIR / f"{options.output_tag}_overlay.mp4"

    segmented_writer = None
    overlay_writer = None
    if not options.disable_write:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        segmented_writer = cv2.VideoWriter(str(segmented_path), fourcc, src_fps, (width, height))
        overlay_writer = cv2.VideoWriter(str(overlay_path), fourcc, src_fps, (width, height))
        if not segmented_writer.isOpened() or not overlay_writer.isOpened():
            capture.release()
            segmented_writer.release()
            overlay_writer.release()
            raise RuntimeError("failed to open output writers")

    warmup_done = 0
    if options.warmup_runs > 0:
        ok_warmup, warmup_frame = capture.read()
        if ok_warmup:
            warmup_tensor = inference_service._preprocess(warmup_frame, model.input_size)
            for _ in range(options.warmup_runs):
                _ = session.run(None, {input_name: warmup_tensor})
                warmup_done += 1
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

    stats = {
        "read": 0.0,
        "preprocess": 0.0,
        "infer": 0.0,
        "postprocess": 0.0,
        "write": 0.0,
        "preview": 0.0,
        "loop_total": 0.0,
        "finalize": 0.0,
    }
    frame_count = 0
    loop_start = time.perf_counter()

    try:
        while True:
            if options.frame_limit > 0 and frame_count >= options.frame_limit:
                break

            t = time.perf_counter()
            ok, frame = capture.read()
            stats["read"] += time.perf_counter() - t
            if not ok:
                break

            frame_count += 1

            t = time.perf_counter()
            input_tensor = inference_service._preprocess(frame, model.input_size)
            stats["preprocess"] += time.perf_counter() - t

            t = time.perf_counter()
            mask, _ = inference_service._infer_mask(session, input_name, input_tensor, model.input_size)
            stats["infer"] += time.perf_counter() - t

            t = time.perf_counter()
            color_mask_input = inference_service._mask_to_color(mask)
            color_mask = cv2.resize(
                color_mask_input,
                (width, height),
                interpolation=cv2.INTER_NEAREST,
            )
            overlay = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)
            stats["postprocess"] += time.perf_counter() - t

            if segmented_writer is not None and overlay_writer is not None:
                t = time.perf_counter()
                segmented_writer.write(color_mask)
                overlay_writer.write(overlay)
                stats["write"] += time.perf_counter() - t

            if not options.disable_preview and options.preview_every > 0:
                if frame_count == 1 or frame_count % options.preview_every == 0:
                    t = time.perf_counter()
                    preview = cv2.resize(overlay, (640, 360), interpolation=cv2.INTER_LINEAR)
                    ok_jpg, encoded = cv2.imencode(".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                    if ok_jpg:
                        _ = base64.b64encode(encoded.tobytes()).decode("ascii")
                    stats["preview"] += time.perf_counter() - t
    finally:
        capture.release()
        if segmented_writer is not None:
            segmented_writer.release()
        if overlay_writer is not None:
            overlay_writer.release()

    stats["loop_total"] = time.perf_counter() - loop_start

    finalize_meta: dict[str, object] = {}
    if frame_count > 0 and not options.disable_write and not options.disable_finalize:
        t = time.perf_counter()
        segmented_meta = finalize_video_for_web(segmented_path, task_tag=f"profile-seg-{options.output_tag}")
        overlay_meta = finalize_video_for_web(overlay_path, task_tag=f"profile-ov-{options.output_tag}")
        stats["finalize"] = time.perf_counter() - t
        finalize_meta = {
            "segmented_codec": segmented_meta.get("codec"),
            "overlay_codec": overlay_meta.get("codec"),
            "segmented_size": segmented_meta.get("size"),
            "overlay_size": overlay_meta.get("size"),
        }

    end_to_end = stats["loop_total"] + stats["finalize"]
    loop_fps = _safe_div(frame_count, stats["loop_total"])
    end_to_end_fps = _safe_div(frame_count, end_to_end)
    infer_only_fps = _safe_div(frame_count, stats["infer"])

    breakdown = {}
    for key in ("read", "preprocess", "infer", "postprocess", "write", "preview"):
        value = stats[key]
        breakdown[key] = {
            "seconds": round(value, 4),
            "pct_of_loop": round(_safe_div(value, stats["loop_total"]) * 100.0, 2),
        }

    return {
        "video": str(options.video),
        "model_key": options.model_key,
        "video_total_frames": total_frames,
        "processed_frames": frame_count,
        "warmup_runs": warmup_done,
        "frame_limit": options.frame_limit,
        "preview_every": options.preview_every,
        "disable_preview": options.disable_preview,
        "disable_write": options.disable_write,
        "disable_finalize": options.disable_finalize,
        "loop_fps": round(loop_fps, 2),
        "end_to_end_fps": round(end_to_end_fps, 2),
        "infer_only_fps": round(infer_only_fps, 2),
        "loop_seconds": round(stats["loop_total"], 4),
        "finalize_seconds": round(stats["finalize"], 4),
        "end_to_end_seconds": round(end_to_end, 4),
        "breakdown": breakdown,
        "finalize_meta": finalize_meta,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Profile realtime video segmentation pipeline stages.")
    parser.add_argument("--video", default="test/assets/sample_video.mp4")
    parser.add_argument("--model-key", default="bisenetv2")
    parser.add_argument("--frames", type=int, default=120, help="Number of frames to profile. <=0 means all.")
    parser.add_argument("--preview-every", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--disable-preview", action="store_true")
    parser.add_argument("--disable-write", action="store_true")
    parser.add_argument("--disable-finalize", action="store_true")
    parser.add_argument("--tag", default=f"profile_{int(time.time())}")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    options = ProfileOptions(
        video=_resolve_video_path(args.video),
        model_key=args.model_key,
        frame_limit=args.frames,
        preview_every=args.preview_every,
        warmup_runs=args.warmup,
        disable_preview=args.disable_preview,
        disable_write=args.disable_write,
        disable_finalize=args.disable_finalize,
        output_tag=args.tag,
    )
    report = run_profile(options)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print("=== Pipeline Profile ===")
    print(f"video: {report['video']}")
    print(f"model: {report['model_key']}")
    print(f"processed_frames: {report['processed_frames']} / total_frames: {report['video_total_frames']}")
    print(f"warmup_runs: {report['warmup_runs']}")
    print(f"loop_fps: {report['loop_fps']}")
    print(f"infer_only_fps: {report['infer_only_fps']}")
    print(f"end_to_end_fps: {report['end_to_end_fps']}")
    print(f"loop_seconds: {report['loop_seconds']}, finalize_seconds: {report['finalize_seconds']}")
    print("\n--- Breakdown (pct_of_loop) ---")
    breakdown = report["breakdown"]
    assert isinstance(breakdown, dict)
    sorted_items = sorted(
        breakdown.items(),
        key=lambda kv: float(kv[1]["seconds"]) if isinstance(kv[1], dict) else 0.0,
        reverse=True,
    )
    for stage, data in sorted_items:
        assert isinstance(data, dict)
        print(f"{stage:>11}: {data['seconds']:>7}s | {data['pct_of_loop']:>6}%")
    if report["finalize_meta"]:
        print("\n--- Finalize Meta ---")
        for key, value in report["finalize_meta"].items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
