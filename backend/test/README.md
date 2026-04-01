# Backend Test Guide

本目录用于后端联调、运行时依赖排查、GPU 冒烟验证、性能瓶颈定位。

## 1. 目录说明

```text
test/
├─ README.md
├─ requirements.no_ort.txt
├─ assets/
│  ├─ test-1.mp4
│  ├─ test-1-short.mp4
│  └─ test-1-tiny.mp4
├─ gpu/
│  ├─ run_bisenet_image.py
│  ├─ check_ort_provider.py
│  └─ check_import_order.py
├─ runtime/
│  ├─ check_path_cuda.py
│  ├─ check_cuda_imports.py
│  ├─ check_dll_load.py
│  ├─ check_ort_capi_dlls.py
│  ├─ check_ort_cleanpath.py
│  └─ check_ort_cuda_missing_deps.py
├─ perf/
│  ├─ make_short_clip.py
│  ├─ profile_video_pipeline.py
│  ├─ profile_realtime_resolution.py
│  ├─ diagnose_fps_bottleneck.py
│  ├─ compare_input_sizes.py
│  ├─ measure_progress_emit_rate.py
│  └─ measure_realtime_ws_fps.py
└─ output/
```

## 2. 依赖与环境

建议使用项目根目录虚拟环境：

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

`test/requirements.no_ort.txt` 用于不依赖 ONNXRuntime 的最小环境准备（部分脚本可用，GPU/推理类脚本不可用）。

## 3. 测试分层

### 3.1 `gpu/`（GPU 冒烟与推理可用性）

- `run_bisenet_image.py`
  - 单图推理（输出 mask/overlay）
  - 可指定 provider（`auto/cpu/cuda`）
  - 可指定 `--extra_dll_dir`（配合 `runtime_dlls`）
- `check_ort_provider.py`
  - 检查 ORT 可用 provider，分别尝试 CUDA-only / CUDA+CPU / CPU-only
- `check_import_order.py`
  - 验证 CUDA 路径注入 + import 顺序是否影响 ORT 初始化

### 3.2 `runtime/`（CUDA/DLL 依赖排障）

- `check_path_cuda.py`
  - 检查 PATH、候选目录、关键 DLL 是否存在
- `check_cuda_imports.py`
  - 查看 `onnxruntime_providers_cuda.dll` 的 import 列表
- `check_dll_load.py`
  - 直接 `ctypes.WinDLL` 验证关键 DLL 可否加载
- `check_ort_capi_dlls.py`
  - 检查 ORT capi 目录核心 DLL 加载情况
- `check_ort_cleanpath.py`
  - 清理冲突 PATH 场景后验证 ORT 会话可否创建
- `check_ort_cuda_missing_deps.py`
  - 逐项定位 provider DLL 缺失依赖

### 3.3 `perf/`（性能与瓶颈定位）

- `make_short_clip.py`
  - 从原视频截取前 N 帧，生成短片用于快速测试
- `profile_video_pipeline.py`
  - 全链路分段剖析（read/preprocess/infer/postprocess/write/preview/finalize）
- `profile_realtime_resolution.py`
  - 模拟 realtime 主循环分段耗时，支持 `--disable-write/--disable-preview`
- `diagnose_fps_bottleneck.py`
  - 场景消融（baseline/no_preview/no_finalize/no_write_no_preview）
- `compare_input_sizes.py`
  - 不改模型权重，仅对比输入尺寸的 FPS 与质量代理指标
- `measure_progress_emit_rate.py`
  - 直接测后端 progress 推送节奏和跨帧步长
- `measure_realtime_ws_fps.py`
  - 走 API + WS 测事件速率与 payload `realtime_fps` 的关系

## 4. 快速开始（推荐流程）

### Step 1：运行时依赖先过一遍

```powershell
.\.venv\Scripts\python .\test\runtime\check_path_cuda.py
.\.venv\Scripts\python .\test\runtime\check_dll_load.py
```

### Step 2：GPU 推理冒烟

```powershell
.\.venv\Scripts\python .\test\gpu\check_ort_provider.py
.\.venv\Scripts\python .\test\gpu\run_bisenet_image.py --provider auto --warmup 1 --repeat 5
```

### Step 3：性能定位（3 分钟内）

```powershell
# 先做短片，减少长时间等待
.\.venv\Scripts\python .\test\perf\make_short_clip.py --input .\test\assets\test-1.mp4 --output .\test\assets\test-1-short.mp4 --frames 90

# 实时链路分段耗时
.\.venv\Scripts\python .\test\perf\profile_realtime_resolution.py --video .\test\assets\test-1-short.mp4 --resolution 256x512 --frames 90 --warmup 0

# 估算写盘开销影响
.\.venv\Scripts\python .\test\perf\profile_realtime_resolution.py --video .\test\assets\test-1-short.mp4 --resolution 256x512 --frames 90 --warmup 0 --disable-write

# 测 WS 推送节奏（默认 max-seconds=180）
.\.venv\Scripts\python .\test\perf\measure_realtime_ws_fps.py --video .\test\assets\test-1-short.mp4 --resolution 256x512 --max-seconds 180
```

## 5. 常用命令清单

### 5.1 输入尺寸对比

```powershell
.\.venv\Scripts\python .\test\perf\compare_input_sizes.py --video .\test\assets\test-1-short.mp4 --model-key bisenetv2 --frames 40 --warmup 10 --sizes "512x1024,384x768,320x640,256x512"
```

### 5.2 场景消融诊断

```powershell
.\.venv\Scripts\python .\test\perf\diagnose_fps_bottleneck.py --video .\test\assets\test-1-short.mp4 --frames 90 --warmup 5 --repeat 2
```

### 5.3 进度推送节奏诊断

```powershell
.\.venv\Scripts\python .\test\perf\measure_progress_emit_rate.py --video .\test\assets\test-1-short.mp4 --resolution 256x512
```

## 6. 产物说明

- `test/output/`
  - GPU 单图测试输出（`*_mask.png`、`*_overlay.png`）
  - 部分 perf 脚本临时视频产物
- `static/result/`
  - 与主服务共享的视频结果目录（某些 perf/profile 脚本会写入）

## 7. 建议的排障顺序

1. 先跑 `runtime`：确认 DLL、PATH、provider 依赖完整
2. 再跑 `gpu`：确认模型可被 CUDA provider 正常执行
3. 再跑 `perf`：拆分 read/pre/infer/post/write/preview/finalize 各阶段开销
4. 若前端观感低于 `realtime_fps`：优先看 `measure_progress_emit_rate.py` 与 WS 推送步长

## 8. 时间控制建议（避免长时间卡住）

- 统一优先使用短视频：`test-1-short.mp4` 或 `test-1-tiny.mp4`
- `measure_realtime_ws_fps.py` 必带 `--max-seconds`（建议 120~180）
- 对耗时高脚本先降低：`--frames`、`--warmup`、`--repeat`




uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
