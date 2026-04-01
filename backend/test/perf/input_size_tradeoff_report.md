# Input Size Tradeoff Report

Date: 2026-03-19

Command:
```powershell
.\.venv\Scripts\python .\test\perf\compare_input_sizes.py --video .\test\assets\sample_video.mp4 --frames 40 --warmup 10 --sizes 512x1024,384x768,320x640,256x512
```

Result:

| size | fps | ms/frame | preprocess(s) | infer(s) | upsample(s) | agreement vs 512x1024 | mIoU vs 512x1024 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 512x1024 | 21.82 | 45.83 | 0.9924 | 0.8312 | 0.0093 | 100.00% | 1.0000 |
| 384x768 | 25.37 | 39.41 | 0.9698 | 0.5999 | 0.0064 | 92.70% | 0.4209 |
| 320x640 | 92.33 | 10.83 | 0.1698 | 0.2598 | 0.0035 | 91.45% | 0.3586 |
| 256x512 | 117.19 | 8.53 | 0.1212 | 0.2153 | 0.0047 | 90.47% | 0.3291 |

Notes:
- This test does not modify model weights; it only changes input resolution.
- `agreement` and `mIoU` are proxy metrics against baseline prediction (512x1024), not ground-truth accuracy.
