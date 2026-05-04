from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import UPLOAD_DIR
from app.services.inference_service import inference_service
from app.services.model_registry import get_model_config


@dataclass
class ProfileStats:
    mode: str
    frames: int
    preprocess_s: float = 0.0
    infer_s: float = 0.0
    postprocess_s: float = 0.0
    overlay_s: float = 0.0
    preview_encode_s: float = 0.0
    total_s: float = 0.0

    @property
    def fps(self) -> float:
        if self.total_s <= 0:
            return 0.0
        return self.frames / self.total_s


def find_latest_video(upload_dir: Path) -> Path:
    videos = [p for p in upload_dir.iterdir() if p.is_file() and p.suffix.lower() in {".mp4", ".avi", ".mov"}]
    if not videos:
        raise FileNotFoundError(f"未在目录中找到视频文件: {upload_dir}")
    return sorted(videos, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def profile_mode(
    video_path: Path,
    mode: str,
    effective_size: tuple[int, int],
    session,
    input_name: str,
    warmup: int,
    measure_frames: int,
) -> ProfileStats:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法读取视频: {video_path}")

    stats = ProfileStats(mode=mode, frames=0)
    frame_idx = 0
    preview_encoded_count = 0

    try:
        while stats.frames < measure_frames:
            ok, frame = cap.read()
            if not ok:
                break

            frame_idx += 1
            if frame_idx <= warmup:
                input_tensor = inference_service._preprocess(frame, effective_size)
                mask, _ = inference_service._infer_mask(session, input_name, input_tensor, effective_size)
                if mode == "current":
                    restored = inference_service._restore_mask_to_size(mask, (frame.shape[0], frame.shape[1]))
                    color_mask = inference_service._mask_to_color(restored)
                    _ = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)
                elif mode == "legacy_approx":
                    color_small = inference_service._mask_to_color(mask)
                    color_mask = inference_service._restore_mask_to_size(color_small, (frame.shape[0], frame.shape[1]))
                    _ = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)
                continue

            t_frame_start = time.perf_counter()

            t0 = time.perf_counter()
            input_tensor = inference_service._preprocess(frame, effective_size)
            stats.preprocess_s += time.perf_counter() - t0

            mask, infer_s = inference_service._infer_mask(session, input_name, input_tensor, effective_size)
            stats.infer_s += infer_s

            overlay = None
            if mode == "current":
                t_post = time.perf_counter()
                restored = inference_service._restore_mask_to_size(mask, (frame.shape[0], frame.shape[1]))
                color_mask = inference_service._mask_to_color(restored)
                stats.postprocess_s += time.perf_counter() - t_post

                t_ov = time.perf_counter()
                overlay = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)
                stats.overlay_s += time.perf_counter() - t_ov

            elif mode == "legacy_approx":
                t_post = time.perf_counter()
                color_small = inference_service._mask_to_color(mask)
                color_mask = inference_service._restore_mask_to_size(color_small, (frame.shape[0], frame.shape[1]))
                stats.postprocess_s += time.perf_counter() - t_post

                t_ov = time.perf_counter()
                overlay = cv2.addWeighted(frame, 0.6, color_mask, 0.4, 0)
                stats.overlay_s += time.perf_counter() - t_ov

            if overlay is not None and (stats.frames % 2 == 0 or stats.frames == 0):
                t_preview = time.perf_counter()
                preview = cv2.resize(overlay, (640, 360), interpolation=cv2.INTER_LINEAR)
                _ = cv2.imencode(".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                stats.preview_encode_s += time.perf_counter() - t_preview
                preview_encoded_count += 1

            stats.total_s += time.perf_counter() - t_frame_start
            stats.frames += 1
    finally:
        cap.release()

    if stats.frames == 0:
        raise RuntimeError("采样帧数为 0，无法分析")

    print(
        f"[DETAIL] mode={mode} frames={stats.frames} preview_encoded={preview_encoded_count} "
        f"pre={stats.preprocess_s/stats.frames:.4f}s infer={stats.infer_s/stats.frames:.4f}s "
        f"post={stats.postprocess_s/stats.frames:.4f}s overlay={stats.overlay_s/stats.frames:.4f}s "
        f"preview={stats.preview_encode_s/stats.frames:.4f}s total={stats.total_s/stats.frames:.4f}s "
        f"fps={stats.fps:.2f}"
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="定位 bisenet fps 下降的只读诊断脚本")
    parser.add_argument("--model", default="bisenetv2", help="模型 key，默认 bisenetv2")
    parser.add_argument("--h", type=int, default=256, help="请求输入高，默认 256")
    parser.add_argument("--w", type=int, default=512, help="请求输入宽，默认 512")
    parser.add_argument("--frames", type=int, default=180, help="用于统计的帧数，默认 180")
    parser.add_argument("--warmup", type=int, default=20, help="预热帧数，默认 20")
    parser.add_argument("--video", default="", help="视频路径，不填则自动取 upload 目录最新视频")
    args = parser.parse_args()

    model = get_model_config(args.model)
    session, input_name = inference_service._session_manager.get(model)

    requested_size = (args.h, args.w)
    effective_size = inference_service._normalize_requested_input_size(session, requested_size)
    providers = session.get_providers()
    input_shape = session.get_inputs()[0].shape

    video_path = Path(args.video) if args.video else find_latest_video(UPLOAD_DIR)
    if not video_path.exists():
        raise FileNotFoundError(f"视频不存在: {video_path}")

    cap_probe = cv2.VideoCapture(str(video_path))
    if not cap_probe.isOpened():
        raise RuntimeError(f"无法读取视频: {video_path}")
    src_w = int(cap_probe.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap_probe.get(cv2.CAP_PROP_FRAME_HEIGHT))
    src_fps = float(cap_probe.get(cv2.CAP_PROP_FPS) or 0.0)
    cap_probe.release()

    print("========== FPS DROP DIAGNOSIS ==========")
    print(f"video={video_path}")
    print(f"source_size={src_h}x{src_w} source_fps={src_fps:.2f}")
    print(f"model={model.model_key} model_default={model.input_size}")
    print(f"requested_size={requested_size} effective_size={effective_size}")
    print(f"onnx_input_shape={input_shape}")
    print(f"providers={providers}")
    print("========================================")

    current_stats = profile_mode(
        video_path=video_path,
        mode="current",
        effective_size=effective_size,
        session=session,
        input_name=input_name,
        warmup=args.warmup,
        measure_frames=args.frames,
    )
    legacy_stats = profile_mode(
        video_path=video_path,
        mode="legacy_approx",
        effective_size=effective_size,
        session=session,
        input_name=input_name,
        warmup=args.warmup,
        measure_frames=args.frames,
    )

    print("\n========== CONCLUSION HINT ==========")
    print(f"current_fps={current_stats.fps:.2f}")
    print(f"legacy_approx_fps={legacy_stats.fps:.2f}")
    print(
        "delta_fps(current-legacy_approx)="
        f"{current_stats.fps - legacy_stats.fps:.2f} (负值表示当前路径更慢)"
    )
    print(
        "主要观察项：1) effective_size 是否被放大 2) providers 是否包含 CUDA "
        "3) postprocess/preview_encode 是否显著占时"
    )
    print("=====================================")


if __name__ == "__main__":
    main()
