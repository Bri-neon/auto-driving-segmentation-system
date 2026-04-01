from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.inference_service import inference_service
from app.services.model_registry import get_model_config


@dataclass
class ScaleResult:
    size: tuple[int, int]  # (h, w)
    processed_frames: int
    fps: float
    ms_per_frame: float
    preprocess_s: float
    infer_s: float
    upsample_s: float
    agreement_pct_vs_baseline: float
    miou_vs_baseline: float


def parse_sizes(text: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for item in text.split(","):
        item = item.strip().lower()
        if not item:
            continue
        if "x" not in item:
            raise ValueError(f"invalid size token: {item}")
        h_str, w_str = item.split("x", 1)
        h = int(h_str)
        w = int(w_str)
        if h <= 0 or w <= 0:
            raise ValueError(f"invalid size value: {item}")
        out.append((h, w))
    if not out:
        raise ValueError("no valid sizes provided")
    return out


def load_frames(video_path: Path, frame_limit: int) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"failed to open video: {video_path}")

    frames: list[np.ndarray] = []
    try:
        while True:
            if frame_limit > 0 and len(frames) >= frame_limit:
                break
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(frame)
    finally:
        cap.release()

    if not frames:
        raise RuntimeError("no frames loaded from video")
    return frames


def mean_iou(pred: np.ndarray, ref: np.ndarray) -> float:
    classes = np.union1d(np.unique(pred), np.unique(ref))
    if classes.size == 0:
        return 1.0

    ious: list[float] = []
    for c in classes.tolist():
        pred_c = pred == c
        ref_c = ref == c
        union = np.logical_or(pred_c, ref_c).sum()
        if union == 0:
            continue
        inter = np.logical_and(pred_c, ref_c).sum()
        ious.append(float(inter / union))

    if not ious:
        return 1.0
    return float(sum(ious) / len(ious))


def run_for_size(
    frames: list[np.ndarray],
    size: tuple[int, int],
    session,
    input_name: str,
    warmup_runs: int,
    baseline_masks: list[np.ndarray] | None,
) -> tuple[ScaleResult, list[np.ndarray]]:
    h, w = size
    preprocess_s = 0.0
    infer_s = 0.0
    upsample_s = 0.0

    # warmup with first frame only; not counted.
    first_tensor = inference_service._preprocess(frames[0], size)
    for _ in range(max(0, warmup_runs)):
        _ = session.run(None, {input_name: first_tensor})

    out_masks: list[np.ndarray] = []
    t_total = time.perf_counter()

    frame_h, frame_w = frames[0].shape[:2]
    for frame in frames:
        t = time.perf_counter()
        input_tensor = inference_service._preprocess(frame, size)
        preprocess_s += time.perf_counter() - t

        t = time.perf_counter()
        mask_input, _ = inference_service._infer_mask(session, input_name, input_tensor, size)
        infer_s += time.perf_counter() - t

        t = time.perf_counter()
        mask_src = cv2.resize(mask_input, (frame_w, frame_h), interpolation=cv2.INTER_NEAREST)
        upsample_s += time.perf_counter() - t

        out_masks.append(mask_src)

    elapsed = time.perf_counter() - t_total
    processed = len(out_masks)
    fps = processed / elapsed if elapsed > 0 else 0.0
    ms_per_frame = (elapsed * 1000.0 / processed) if processed > 0 else 0.0

    if baseline_masks is None:
        agreement_pct = 100.0
        miou = 1.0
    else:
        agreements = []
        mious = []
        for pred, ref in zip(out_masks, baseline_masks):
            agreements.append(float((pred == ref).mean() * 100.0))
            mious.append(mean_iou(pred, ref))
        agreement_pct = float(sum(agreements) / len(agreements)) if agreements else 0.0
        miou = float(sum(mious) / len(mious)) if mious else 0.0

    return (
        ScaleResult(
            size=size,
            processed_frames=processed,
            fps=round(fps, 2),
            ms_per_frame=round(ms_per_frame, 2),
            preprocess_s=round(preprocess_s, 4),
            infer_s=round(infer_s, 4),
            upsample_s=round(upsample_s, 4),
            agreement_pct_vs_baseline=round(agreement_pct, 2),
            miou_vs_baseline=round(miou, 4),
        ),
        out_masks,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare input sizes without changing model weights (FPS + quality proxy)."
    )
    parser.add_argument("--video", default="test/assets/sample_video.mp4")
    parser.add_argument("--model-key", default="bisenetv2")
    parser.add_argument("--frames", type=int, default=40)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument(
        "--sizes",
        default="512x1024,384x768,320x640,256x512",
        help="comma-separated HxW list; first successful size is baseline",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        raise FileNotFoundError(f"video not found: {video_path}")

    sizes = parse_sizes(args.sizes)
    frames = load_frames(video_path, args.frames)

    model = get_model_config(args.model_key)
    session, input_name = inference_service._session_manager.get(model)

    results: list[ScaleResult] = []
    failures: list[dict[str, str]] = []

    baseline_masks: list[np.ndarray] | None = None
    baseline_size: tuple[int, int] | None = None

    for size in sizes:
        try:
            result, masks = run_for_size(
                frames=frames,
                size=size,
                session=session,
                input_name=input_name,
                warmup_runs=args.warmup,
                baseline_masks=baseline_masks,
            )
            if baseline_masks is None:
                baseline_masks = masks
                baseline_size = size
            results.append(result)
        except Exception as ex:
            failures.append({"size": f"{size[0]}x{size[1]}", "error": str(ex)})

    if not results:
        raise RuntimeError(f"all sizes failed: {failures}")

    if args.json:
        payload = {
            "video": str(video_path),
            "frames": len(frames),
            "model_key": args.model_key,
            "baseline_size": f"{baseline_size[0]}x{baseline_size[1]}" if baseline_size else None,
            "results": [
                {
                    "size": f"{r.size[0]}x{r.size[1]}",
                    "processed_frames": r.processed_frames,
                    "fps": r.fps,
                    "ms_per_frame": r.ms_per_frame,
                    "preprocess_s": r.preprocess_s,
                    "infer_s": r.infer_s,
                    "upsample_s": r.upsample_s,
                    "agreement_pct_vs_baseline": r.agreement_pct_vs_baseline,
                    "miou_vs_baseline": r.miou_vs_baseline,
                }
                for r in results
            ],
            "failures": failures,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print("=== Input Size Comparison ===")
    print(f"video: {video_path}")
    print(f"model: {args.model_key}")
    print(f"frames: {len(frames)}")
    if baseline_size:
        print(f"baseline size: {baseline_size[0]}x{baseline_size[1]}")

    print(
        "\n{:<10} {:>7} {:>10} {:>10} {:>10} {:>10} {:>12} {:>10}".format(
            "size", "fps", "ms/frame", "prep(s)", "infer(s)", "up(s)", "agree(%)", "mIoU"
        )
    )
    print("-" * 90)
    for r in results:
        size_str = f"{r.size[0]}x{r.size[1]}"
        print(
            "{:<10} {:>7.2f} {:>10.2f} {:>10.4f} {:>10.4f} {:>10.4f} {:>12.2f} {:>10.4f}".format(
                size_str,
                r.fps,
                r.ms_per_frame,
                r.preprocess_s,
                r.infer_s,
                r.upsample_s,
                r.agreement_pct_vs_baseline,
                r.miou_vs_baseline,
            )
        )

    if failures:
        print("\n--- Failures ---")
        for item in failures:
            print(f"{item['size']}: {item['error']}")


if __name__ == "__main__":
    main()
