from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from profile_video_pipeline import ProfileOptions, run_profile


def _run_case(
    video: Path,
    frames: int,
    model_key: str,
    warmup: int,
    case: str,
    run_index: int,
) -> dict[str, object]:
    now = int(time.time())
    common = {
        "video": video,
        "model_key": model_key,
        "frame_limit": frames,
        "preview_every": 3,
        "warmup_runs": warmup,
        "output_tag": f"diag_{case}_{run_index}_{now}",
    }
    if case == "baseline":
        return run_profile(
            ProfileOptions(
                **common,
                disable_preview=False,
                disable_write=False,
                disable_finalize=False,
            )
        )
    if case == "no_preview":
        return run_profile(
            ProfileOptions(
                **common,
                disable_preview=True,
                disable_write=False,
                disable_finalize=False,
            )
        )
    if case == "no_finalize":
        return run_profile(
            ProfileOptions(
                **common,
                disable_preview=False,
                disable_write=False,
                disable_finalize=True,
            )
        )
    if case == "no_write_no_preview":
        return run_profile(
            ProfileOptions(
                **common,
                disable_preview=True,
                disable_write=True,
                disable_finalize=True,
            )
        )
    raise ValueError(f"unknown case: {case}")


def _avg_reports(items: list[dict[str, object]]) -> dict[str, object]:
    if not items:
        raise ValueError("empty reports")

    n = len(items)

    def avg_num(key: str) -> float:
        return sum(float(it[key]) for it in items) / n

    base = items[-1].copy()
    base["loop_fps"] = round(avg_num("loop_fps"), 2)
    base["end_to_end_fps"] = round(avg_num("end_to_end_fps"), 2)
    base["infer_only_fps"] = round(avg_num("infer_only_fps"), 2)
    base["loop_seconds"] = round(avg_num("loop_seconds"), 4)
    base["finalize_seconds"] = round(avg_num("finalize_seconds"), 4)
    base["end_to_end_seconds"] = round(avg_num("end_to_end_seconds"), 4)

    breakdown_avg: dict[str, dict[str, float]] = {}
    for stage in ("read", "preprocess", "infer", "postprocess", "write", "preview"):
        stage_seconds = 0.0
        stage_pct = 0.0
        for report in items:
            b = report["breakdown"]
            assert isinstance(b, dict)
            d = b[stage]
            assert isinstance(d, dict)
            stage_seconds += float(d["seconds"])
            stage_pct += float(d["pct_of_loop"])
        breakdown_avg[stage] = {
            "seconds": round(stage_seconds / n, 4),
            "pct_of_loop": round(stage_pct / n, 2),
        }
    base["breakdown"] = breakdown_avg
    base["runs"] = n
    return base


def _summary_line(name: str, report: dict[str, object]) -> str:
    loop_fps = report["loop_fps"]
    end_to_end_fps = report["end_to_end_fps"]
    infer_only_fps = report["infer_only_fps"]
    finalize_seconds = report["finalize_seconds"]
    runs = report.get("runs", 1)
    return (
        f"{name:>18} | runs={runs} | loop_fps={loop_fps:>6} | end_to_end_fps={end_to_end_fps:>6} "
        f"| infer_only_fps={infer_only_fps:>6} | finalize_s={finalize_seconds:>6}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bottleneck diagnosis by scenario ablation.")
    parser.add_argument("--video", default="test/assets/sample_video.mp4")
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--model-key", default="bisenetv2")
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    video = Path(args.video)
    if not video.exists():
        raise FileNotFoundError(f"video not found: {video}")

    cases = ["baseline", "no_preview", "no_finalize", "no_write_no_preview"]
    reports: dict[str, dict[str, object]] = {}
    raw_runs: dict[str, list[dict[str, object]]] = {}

    for case in cases:
        raw_runs[case] = []
        for i in range(max(1, args.repeat)):
            print(f"[RUN] {case} ({i + 1}/{max(1, args.repeat)})")
            one = _run_case(
                video=video,
                frames=args.frames,
                model_key=args.model_key,
                warmup=args.warmup,
                case=case,
                run_index=i,
            )
            raw_runs[case].append(one)
        reports[case] = _avg_reports(raw_runs[case])

    base = reports["baseline"]
    no_preview = reports["no_preview"]
    no_finalize = reports["no_finalize"]
    no_write_no_preview = reports["no_write_no_preview"]

    print("\n=== Scenario FPS Summary (Averaged) ===")
    for case in cases:
        print(_summary_line(case, reports[case]))

    print("\n=== Impact Estimation ===")
    print(
        "preview_overhead_fps_gain:",
        round(float(no_preview["loop_fps"]) - float(base["loop_fps"]), 2),
    )
    print(
        "finalize_overhead_fps_gain:",
        round(float(no_finalize["end_to_end_fps"]) - float(base["end_to_end_fps"]), 2),
    )
    print(
        "write_plus_preview_overhead_fps_gain:",
        round(float(no_write_no_preview["loop_fps"]) - float(base["loop_fps"]), 2),
    )

    base_breakdown = base["breakdown"]
    assert isinstance(base_breakdown, dict)
    sorted_stages = sorted(
        base_breakdown.items(),
        key=lambda kv: float(kv[1]["seconds"]) if isinstance(kv[1], dict) else 0.0,
        reverse=True,
    )
    print("\n=== Baseline Stage Ranking ===")
    for stage, data in sorted_stages:
        assert isinstance(data, dict)
        print(f"{stage:>11}: {data['seconds']:>7}s | {data['pct_of_loop']:>6}%")

    if args.json:
        print("\n=== JSON (Averaged) ===")
        print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
