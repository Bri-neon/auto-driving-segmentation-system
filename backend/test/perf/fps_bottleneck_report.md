# FPS Bottleneck Report

Date: 2026-03-19

## Commands Run

```powershell
.\.venv\Scripts\python .\test\perf\diagnose_fps_bottleneck.py --video .\test\assets\sample_video.mp4 --frames 40 --warmup 20 --repeat 3 --model-key bisenetv2
.\.venv\Scripts\python .\test\perf\profile_video_pipeline.py --video .\test\assets\sample_video.mp4 --frames 0 --warmup 20 --preview-every 3 --tag deep_baseline --json
.\.venv\Scripts\python .\test\perf\profile_video_pipeline.py --video .\test\assets\sample_video.mp4 --frames 0 --warmup 20 --disable-write --disable-preview --disable-finalize --tag deep_nowrite --json
.\.venv\Scripts\python .\test\perf\profile_video_pipeline.py --video .\test\assets\sample_video.mp4 --frames 0 --warmup 20 --disable-finalize --tag deep_nofinalize --json
```

## Stable Result (repeat=3 average, 40 frames)

- baseline: `loop_fps=10.01`, `end_to_end_fps=8.49`, `infer_only_fps=34.73`
- no_preview: `loop_fps=10.62`
- no_finalize: `end_to_end_fps=9.73`
- no_write_no_preview: `loop_fps=11.86`

Impact estimation:
- preview overhead gain: `+0.61 fps`
- finalize overhead gain: `+1.24 fps`
- write + preview overhead gain: `+1.85 fps`

## Baseline Stage Breakdown (loop only)

- preprocess: `30.20%`
- infer: `29.10%`
- postprocess: `22.21%`
- write: `12.72%`
- read: `3.42%`
- preview (JPEG/base64): `1.31%`

## Conclusion

Main loop bottleneck is dominated by the compute pipeline itself (`preprocess + infer + postprocess ~= 81.51%`).

`write` cost is meaningful but secondary (`~12.72%`).

`preview` serialization (`resize + jpeg + base64`) is not the main bottleneck at current send rate (`preview_every=3`).

Finalization/transcode hurts end-to-end throughput but does not affect in-loop smoothness while frames are being processed.
