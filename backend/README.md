# 自动驾驶图像语义分割系统（后端）

> 基于 **FastAPI + ONNX Runtime + OpenCV** 的语义分割后端服务。  
> 支持图像分割、视频同步分割、视频二阶段流程（`realtime -> finalize -> result`）、模型切换、分辨率切换、WebSocket 实时预览推送。

## 1. 项目定位

本项目是《基于卷积神经网络的自动驾驶图像语义分割系统设计与实现》的后端核心工程，重点能力：

- 图像上传 + 语义分割推理 + 分割图/融合图输出。
- 视频同步接口：一次请求完成整段视频推理并返回最终结果。
- 视频二阶段接口：
  - 第一阶段 `realtime`：实时预览与进度推送（WebSocket）。
  - 第二阶段 `finalize`：后台生成最终可播放视频。
  - `result` 查询最终生成状态和 URL。
- 支持模型切换（DeepLabV3+ / BiSeNetV2）。
- 支持输入分辨率切换（4 档预设）。
- 支持统一日志、请求追踪、统一异常响应、静态资源托管。

---

## 2. 技术栈与关键依赖

当前 `requirements.txt` 主要依赖：

- `fastapi==0.116.1`
- `uvicorn[standard]==0.35.0`
- `pydantic==2.11.7`
- `onnxruntime-gpu`（本地 wheel：`onnxruntime_gpu-1.17.1-cp310-cp310-win_amd64.whl`）
- `opencv-python==4.11.0.86`
- `numpy==1.26.4`
- `python-multipart==0.0.20`
- `imageio-ffmpeg==0.6.0`
- `httpx==0.28.1`

---

## 3. 快速启动

### 3.1 创建虚拟环境（Python 3.10）

```bash
cd d:\auto-driving-segmentation-system\backend
py -3.10 -m venv .venv
```

### 3.2 安装依赖

```bash
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 3.3 启动服务

```bash
.\.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

OpenAPI 文档：

- Swagger：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

---

## 4. 项目结构（核心）

```text
backend/
├─ app/
│  ├─ api/routers/
│  │  ├─ health.py
│  │  ├─ model.py
│  │  └─ segment.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ exceptions.py
│  │  ├─ logger.py
│  │  └─ responses.py
│  ├─ schemas/
│  │  ├─ common.py
│  │  ├─ model.py
│  │  └─ segment.py
│  ├─ services/
│  │  ├─ inference_service.py
│  │  ├─ model_registry.py
│  │  ├─ resolution_service.py
│  │  └─ video_realtime_service.py
│  ├─ utils/
│  │  ├─ file_utils.py
│  │  └─ video_utils.py
│  └─ main.py
├─ models/
├─ runtime_dlls/
├─ static/
│  ├─ upload/
│  └─ result/
├─ test/
├─ requirements.txt
├─ README.md
└─ main.py
```

---

## 5. 配置说明

配置文件：`app/core/config.py`

- `api_prefix`: 默认 `/api`
- `static_url_prefix`: 默认 `/static`
- `default_model_key`: 默认 `bisenetv2`
- `max_upload_size_mb`: 默认 `100`
- `cors_origins`: 默认允许
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`

环境变量：

- `DEFAULT_MODEL_KEY`：覆盖默认模型
- `MAX_UPLOAD_SIZE_MB`：覆盖上传大小限制
- `CUDA_BIN_PATH`：可选，指定 CUDA `bin` 目录用于 DLL 搜索

---

## 6. 模型与推理路径

模型注册位置：`app/services/model_registry.py`

当前模型：

- `deeplabv3plus_resnet50`
  - 展示名：`DeepLabV3+ ResNet50 FP16`
  - 默认输入：`512x512`
  - 文件：`models/deeplabv3plus_resnet50_fp16.onnx`
- `bisenetv2`
  - 展示名：`BiSeNetV2 FP16`
  - 默认输入：`512x1024`
  - 文件：`models/bisenetv2_fp16.onnx`

推理实现：`app/services/inference_service.py`

- `segment_image(...)`：图像分割
- `segment_video(...)`：视频分割（同步）
- ONNX Runtime 优先 `CUDAExecutionProvider`，失败自动回退 `CPUExecutionProvider`

---

## 7. 分辨率能力

分辨率服务：`app/services/resolution_service.py`

支持固定 4 档：

- `512x1024`
- `384x768`
- `320x640`
- `256x512`

接口：`GET /api/segment/resolutions`

说明：

- `resolution` 不传时，使用模型默认输入尺寸。
- 传值非法会返回 400（带可选项提示）。

---

## 8. 统一响应格式

统一响应模型：`app/schemas/common.py`

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

- 成功：`code=0`
- 业务异常：`AppException`，`code` 默认为 `1001`
- 全局异常处理：`app/core/exceptions.py`

---

## 9. API 清单

### 9.1 健康检查

- `GET /api/health`

### 9.2 模型信息

- `GET /api/model/info?model_key=bisenetv2`

### 9.3 分辨率列表

- `GET /api/segment/resolutions`

### 9.4 图像分割

- `POST /api/segment`
- `form-data`
  - `file`（必填）
  - `model_key`（可选）
  - `resolution`（可选）

### 9.5 视频分割（同步）

- `POST /api/segment/video`
- `form-data`
  - `file`（必填）
  - `model_key`（可选）
  - `resolution`（可选）

### 9.6 视频分割（实时阶段）

- `POST /api/segment/video/realtime`
- `form-data`
  - `file`（必填）
  - `model_key`（可选）
  - `resolution`（可选）
- 返回字段（核心）
  - `task_id`
  - `ws_url`
  - `status`
  - `finalize_status`
  - `original_video_url`
  - `segmented_video_url`
  - `overlay_video_url`
  - `model_name`
  - `input_size`

### 9.7 触发最终视频生成

- `POST /api/segment/video/finalize/{task_id}`
- 返回字段（核心）
  - `task_id`
  - `realtime_status`
  - `finalize_status`
  - `message`

### 9.8 查询最终视频结果

- `GET /api/segment/video/result/{task_id}`
- 返回字段（核心）
  - `task_id`
  - `realtime_status`
  - `finalize_status`
  - `summary`
  - `result`
  - `message`

### 9.9 WebSocket 实时预览

- `WS /api/segment/video/ws/{task_id}`

事件类型（实时阶段）：

- `task_snapshot`
- `task_started`
- `task_progress`
- `task_completed`
- `task_failed`

说明：

- 当前设计中，WS 在 `task_completed/task_failed` 后会关闭。
- `finalize` 阶段建议走 REST（`finalize` + `result` 轮询）。

---

## 10. 视频二阶段流程（后端视角）

### 10.1 目标

- 实时阶段优先“观感和反馈速度”
- 最终阶段保证“文件可播放性与兼容性”

### 10.2 状态机

实时阶段状态：

- `queued -> running -> completed/failed`

最终阶段状态：

- `idle -> queued -> running -> completed/failed`

### 10.3 典型调用顺序

1. `POST /api/segment/video/realtime`
2. `WS /api/segment/video/ws/{task_id}` 接收进度/预览
3. 收到 `task_completed` 后，调用 `POST /api/segment/video/finalize/{task_id}`
4. 轮询 `GET /api/segment/video/result/{task_id}` 直到 `finalize_status=completed`
5. 播放 `result.overlay_video_url`

---

## 11. 视频可播放保障机制

位置：`app/utils/video_utils.py`

最终视频生成时会执行：

1. `ffmpeg` 转码：`libx264 + yuv420p + faststart`
2. 文件替换覆盖
3. `OpenCV` 基本可读校验
4. 编码检查（要求 `h264/avc1`）

这能明显降低浏览器出现 `0:00` 黑框不可播的概率。

---

## 12. 日志与请求追踪

- 日志器：`app/core/logger.py`
- 中间件会注入 `X-Request-ID`
- 每个请求会记录：`method/path/status/elapsed`
- 上传过大、异常堆栈、任务失败会有单独 warning/error 日志

---

## 13. 静态文件与产物路径

服务静态前缀：`/static`

- 上传文件：`/static/upload/...`
- 结果文件：`/static/result/...`

对应磁盘目录：

- `static/upload/`
- `static/result/`

---

## 14. 文件上传校验

位置：`app/utils/file_utils.py`

校验维度：

- 文件扩展名
- MIME 类型
- 分块写入时累计大小（超限立即报错）

默认允许：

- 图片：`.jpg/.jpeg/.png`
- 视频：`.mp4/.avi/.mov`

---

## 15. CUDA / DLL 说明（Windows）

推理服务会在启动模型时尝试补充 DLL 搜索路径：

- `runtime_dlls/`
- `CUDA_BIN_PATH` 指向目录（可选）
- `onnxruntime/capi`

`runtime_dlls/` 使用说明见：`runtime_dlls/README.md`

---

## 16. 测试体系（test 目录）

测试文档：`test/README.md`

分层：

- `test/gpu`：GPU/Provider 冒烟
- `test/runtime`：DLL 与 CUDA 依赖排查
- `test/perf`：性能分解、FPS瓶颈定位、WS事件频率测量
- `test/assets`：测试视频素材

示例命令：

```bash
# GPU 单图推理冒烟
.\.venv\Scripts\python .\test\gpu\run_bisenet_image.py --provider auto --warmup 1 --repeat 5

# 生成短视频，便于快速性能测试
.\.venv\Scripts\python .\test\perf\make_short_clip.py --input .\test\assets\test-1.mp4 --output .\test\assets\test-1-short.mp4 --frames 90

# 实时链路分段耗时分析
.\.venv\Scripts\python .\test\perf\profile_realtime_resolution.py --video .\test\assets\test-1-short.mp4 --resolution 256x512 --frames 90 --warmup 0
```

---

## 17. 常见问题（FAQ）

### 17.1 为什么前端实时预览 FPS 和后端 `realtime_fps` 不一致？

因为预览是“事件推送 + 前端渲染”链路，不等于纯推理速度。当前后端预览事件有节流策略，且前端还会做渲染调度。

### 17.2 为什么 `avg_fps` 看起来低？

`avg_fps` 包含完整链路开销（读帧/预处理/后处理/编码/写盘/转码），而不仅是模型前向推理。

### 17.3 为什么实时完成后还要 finalize？

二阶段设计用于把“实时反馈”与“最终可播放结果生成”解耦，前者强调响应，后者强调产物质量与兼容性。

### 17.4 上传失败提示文件类型不支持

检查：

- 扩展名是否在允许列表
- 浏览器上传 MIME 是否匹配

---

## 18. 开发建议

- 新增接口时，先补 `schemas`，再补 `router` 与 `service`。
- 视频链路改动优先保持 `realtime/finalize` 状态分离。
- 性能优化先靠 `test/perf` 做分段定位，避免盲改。
- 若要进一步提升实时观感，优先优化预览编码策略与推送频率，而不是只看模型单帧推理耗时。

---

## 19. 许可证与说明

本仓库用于毕业设计演示与研发验证。  
如需开源发布，建议补充：许可证、贡献指南、隐私与数据处理声明。

---

## 20. 登录与历史记录（2026-04 更新）

后端已新增 MySQL 持久化的用户与历史记录能力：

- 用户注册、登录、JWT 鉴权、当前用户信息、头像上传
- 图像/视频推理历史自动入库（含 realtime/finalize 状态）
- 历史分页查询、历史详情、历史删除
- 推理接口改为登录保护（`/api/segment/resolutions` 保持公开）

数据库默认连接（可用环境变量覆盖）：

- `DB_HOST`（默认 `127.0.0.1`）
- `DB_PORT`（默认 `3306`）
- `DB_USER`（默认 `root`）
- `DB_PASSWORD`（默认 `123456`）
- `DB_NAME`（默认 `segmentation_system`）
- `JWT_SECRET_KEY`
- `JWT_EXPIRE_MINUTES`

初始化数据库：

```bash
.\.venv\Scripts\python .\scripts\init_mysql_auth.py --host 127.0.0.1 --port 3306 --user root --password 123456
```

前端联调接口文档见：

- `docs/frontend_api_integration.md`
