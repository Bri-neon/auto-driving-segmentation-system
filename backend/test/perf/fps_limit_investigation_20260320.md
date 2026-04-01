# FPS Limit Investigation (2026-03-20)

## Scope
Only test scripts were used/added. No production code changes outside `test/`.

## New helper scripts
- `test/perf/make_short_clip.py`
- `test/perf/profile_realtime_resolution.py`
- `test/perf/measure_progress_emit_rate.py`
- updated `test/perf/measure_realtime_ws_fps.py` with safer termination logic

## Key evidence

### 1) Same video + same resolution, pure compute can be high
Command:
`python test/perf/compare_input_sizes.py --video test/assets/test-1-short.mp4 --frames 90 --warmup 10 --sizes 256x512`

Result:
- `256x512 -> 56.36 FPS` (no video write path)

### 2) Real API path is much lower
Command:
`POST /api/segment/video` with `resolution=256x512` on `test-1-short.mp4`

Result samples:
- run1: `avg_fps=8.0`, `realtime_fps=12.4`
- run2: `avg_fps=9.1`, `realtime_fps=11.4`

### 3) Why lower: realtime-like stage profile
Command:
`python test/perf/profile_realtime_resolution.py --video test/assets/test-1-short.mp4 --resolution 256x512 --frames 90 --warmup 0`

Result:
- overall `8.06 FPS`
- stage ratio:
  - infer: `38.14%`
  - write: `33.99%`
  - post: `14.25%`
  - pre: `5.83%`
  - read: `6.69%`
  - preview: `0.89%`

Command (disable write):
`python test/perf/profile_realtime_resolution.py --video test/assets/test-1-short.mp4 --resolution 256x512 --frames 90 --warmup 10 --disable-write`

Result:
- `48.07 FPS`

Interpretation:
- dual 1080p write is a major limiter
- preview JPEG/base64 is small

### 4) Why frontend preview looks very low
Command:
`python test/perf/measure_progress_emit_rate.py --video test/assets/test-1-short.mp4 --resolution 256x512`

Result:
- payload realtime_fps avg: `11.15`
- avg frame step per progress event: `2.97`
- progress event rate: `3.44 fps`

Interpretation:
- backend emits progress roughly every 3 frames, so preview event FPS ~= realtime_fps / 3.
- if realtime_fps is ~10-12, frontend preview naturally feels ~3-4 fps.

## Root cause summary
1) cold-start / warmup effect is large on short videos
2) two full-HD video writes per frame consume a large share
3) progress push is intentionally every 3 frames, so preview FPS is much lower than model loop FPS

These explain why offline/pure tests can show very high numbers while real frontend experience stays around/below 10.
