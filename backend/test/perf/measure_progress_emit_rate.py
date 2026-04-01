from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.model_registry import get_model_config
from app.services.resolution_service import parse_resolution_or_default
from app.services.video_realtime_service import video_realtime_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure backend progress emit cadence directly.")
    parser.add_argument("--video", default="test/assets/test-1-short.mp4")
    parser.add_argument("--model-key", default="bisenetv2")
    parser.add_argument("--resolution", default="256x512")
    args = parser.parse_args()

    video = Path(args.video)
    if not video.exists():
        raise FileNotFoundError(f"video not found: {video}")

    model = get_model_config(args.model_key)
    input_size = parse_resolution_or_default(args.resolution, model.input_size)

    recorded: list[tuple[float, dict]] = []
    original_broadcast = video_realtime_service._broadcast_threadsafe

    def fake_broadcast(loop, task_id: str, payload: dict) -> None:
        recorded.append((time.perf_counter(), payload))

    video_realtime_service._broadcast_threadsafe = fake_broadcast

    try:
        task = video_realtime_service.create_task(
            model=model,
            input_size=input_size,
            original_video_url=f"/static/upload/{video.name}",
            original_video_path=video,
            segmented_filename=f"diag_emit_{int(time.time())}_mask.mp4",
            overlay_filename=f"diag_emit_{int(time.time())}_overlay.mp4",
        )
        loop = asyncio.new_event_loop()
        t0 = time.perf_counter()
        video_realtime_service._run_task_sync(task.task_id, loop)
        elapsed = time.perf_counter() - t0
    finally:
        video_realtime_service._broadcast_threadsafe = original_broadcast

    progress = [(t, p) for t, p in recorded if p.get("type") == "task_progress"]
    terminal = next((p for _, p in recorded if p.get("type") in {"task_completed", "task_failed"}), None)

    frame_steps = []
    payload_fps = []
    last_frame = None
    for _, p in progress:
        fi = int(p.get("frame_index", 0))
        if last_frame is not None and fi >= last_frame:
            frame_steps.append(fi - last_frame)
        last_frame = fi
        try:
            payload_fps.append(float(p.get("realtime_fps", 0.0)))
        except Exception:
            pass

    if len(progress) >= 2:
        progress_span = progress[-1][0] - progress[0][0]
    else:
        progress_span = 0.0

    progress_event_rate = (len(progress) / progress_span) if progress_span > 0 else 0.0
    avg_payload_fps = statistics.mean(payload_fps) if payload_fps else 0.0
    avg_step = statistics.mean(frame_steps) if frame_steps else 0.0

    print("=== Progress Emit Rate Diagnosis ===")
    print("video:", video)
    print("input_size:", input_size)
    print("elapsed_s:", round(elapsed, 3))
    print("events_total:", len(recorded))
    print("progress_events:", len(progress))
    print("progress_event_rate_fps:", round(progress_event_rate, 2))
    print("payload_realtime_fps_avg:", round(avg_payload_fps, 2))
    print("avg_frame_step_per_progress_event:", round(avg_step, 2))

    if avg_payload_fps > 0 and avg_step > 0:
        print("payload_fps_div_step:", round(avg_payload_fps / avg_step, 2))

    if terminal:
        print("terminal_type:", terminal.get("type"))
        if terminal.get("type") == "task_completed":
            result = terminal.get("result", {})
            print("result_avg_fps:", result.get("avg_fps"))
            print("result_realtime_fps:", result.get("realtime_fps"))


if __name__ == "__main__":
    main()
