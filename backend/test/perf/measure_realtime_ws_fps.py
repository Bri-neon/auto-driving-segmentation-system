from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure realtime WS progress event rate and compare with payload realtime_fps."
    )
    parser.add_argument("--video", default="test/assets/test-1-short.mp4")
    parser.add_argument("--model-key", default="bisenetv2")
    parser.add_argument("--resolution", default="256x512")
    parser.add_argument("--max-events", type=int, default=99999)
    parser.add_argument("--max-seconds", type=float, default=180.0)
    args = parser.parse_args()

    video = Path(args.video)
    if not video.exists():
        raise FileNotFoundError(f"video not found: {video}")

    client = TestClient(app)

    with video.open("rb") as f:
        resp = client.post(
            "/api/segment/video/realtime",
            files={"file": (video.name, f, "video/mp4")},
            data={"model_key": args.model_key, "resolution": args.resolution},
        )
    if resp.status_code != 200:
        raise RuntimeError(f"init failed: {resp.status_code} {resp.text}")

    init = resp.json()["data"]
    task_id = init["task_id"]
    ws_url = init["ws_url"]

    events = 0
    progress_events = 0
    first_progress_t = None
    last_progress_t = None
    payload_fps: list[float] = []
    frame_delta_sum = 0
    frame_prev = 0
    terminal = None
    terminal_result = None

    start = time.perf_counter()
    with client.websocket_connect(ws_url) as ws:
        while True:
            if (time.perf_counter() - start) >= args.max_seconds:
                terminal = "timeout"
                break

            try:
                msg = ws.receive_json()
            except Exception as ex:
                terminal = f"ws_closed:{type(ex).__name__}"
                break

            events += 1
            et = msg.get("type")

            if et == "task_snapshot":
                status = str(msg.get("status", ""))
                if status in {"completed", "failed"}:
                    terminal = f"snapshot_{status}"
                    if status == "completed" and msg.get("result"):
                        terminal_result = {"result": msg.get("result")}
                    break

            if et == "task_progress":
                progress_events += 1
                now = time.perf_counter()
                if first_progress_t is None:
                    first_progress_t = now
                last_progress_t = now

                fi = int(msg.get("frame_index", 0))
                if frame_prev > 0 and fi >= frame_prev:
                    frame_delta_sum += fi - frame_prev
                frame_prev = fi

                try:
                    payload_fps.append(float(msg.get("realtime_fps", 0.0)))
                except Exception:
                    pass

                if progress_events >= args.max_events:
                    terminal = "manual_stop"
                    break

            if et in {"task_completed", "task_failed"}:
                terminal = et
                terminal_result = msg
                break

    end = time.perf_counter()
    elapsed = end - start

    push_elapsed = 0.0
    if first_progress_t is not None and last_progress_t is not None:
        push_elapsed = max(0.0, last_progress_t - first_progress_t)

    progress_event_rate = (progress_events / push_elapsed) if push_elapsed > 0 else 0.0
    payload_avg = statistics.mean(payload_fps) if payload_fps else 0.0
    payload_max = max(payload_fps) if payload_fps else 0.0
    frame_step_avg = (frame_delta_sum / max(1, progress_events - 1)) if progress_events > 1 else 0.0

    print("=== Realtime WS FPS Measure ===")
    print("task_id:", task_id)
    print("resolution:", args.resolution)
    print("input_size_from_init:", init.get("input_size"))
    print("terminal:", terminal)
    print("elapsed_s:", round(elapsed, 3))
    print("events_total:", events)
    print("progress_events:", progress_events)
    print("progress_event_rate_fps:", round(progress_event_rate, 2))
    print("payload_realtime_fps_avg:", round(payload_avg, 2))
    print("payload_realtime_fps_max:", round(payload_max, 2))
    print("avg_frame_step_per_progress_event:", round(frame_step_avg, 2))

    if payload_avg > 0 and frame_step_avg > 0:
        expected_event_rate = payload_avg / frame_step_avg
        print("expected_progress_event_rate_by_payload:", round(expected_event_rate, 2))

    if terminal_result and "result" in terminal_result:
        result = terminal_result.get("result", {})
        print("result_avg_fps:", result.get("avg_fps"))
        print("result_realtime_fps:", result.get("realtime_fps"))
        print("result_input_size:", result.get("input_size"))


if __name__ == "__main__":
    main()
