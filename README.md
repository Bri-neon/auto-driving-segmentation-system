# Auto Driving Segmentation System — 自动驾驶图像语义分割系统

基于 Vue 3 + FastAPI + ONNX Runtime 的全栈自动驾驶语义分割平台，支持图像与视频的 Cityscapes 19 类道路场景分割，集成实时 WebSocket 推流与二阶段视频生成流水线。

## 技术栈

### 前端

| 技术 | 用途 |
|------|------|
| Vue 3 (Composition API) | 框架 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| Pinia | 状态管理（视频实时任务状态机） |
| Vue Router | 路由 & 权限守卫 |
| Element Plus | UI 组件库 |
| Axios | HTTP 请求封装（拦截器 + JWT 注入） |

### 后端

| 技术 | 用途 |
|------|------|
| FastAPI | Web 框架（REST + WebSocket） |
| ONNX Runtime | GPU/CUDA 深度学习推理引擎 |
| OpenCV | 图像/视频帧处理 |
| NumPy | 张量运算 & 调色板映射 |
| Pydantic v2 | 数据校验 |
| PyJWT | JWT 鉴权 |
| MySQL (pymysql) | 数据库 |
| imageio-ffmpeg | 视频转码封装 |

### 模型

| 模型 | 输入尺寸 | 数据集 |
|------|----------|--------|
| DeepLabV3+ ResNet50 FP16 | 512×512 | Cityscapes（19 类） |
| BiSeNetV2 FP16 | 512×1024 | Cityscapes（19 类） |

## 项目结构

```
auto-driving-segmentation-system/
├── frontend/
│   └── front/                  # Vue 3 前端项目
│       └── src/
│           ├── api/             # 接口封装（auth/segment/history/admin/model）
│           ├── components/      # 组件（UploadPanel/ResultDisplay/VideoResultPanel/...）
│           ├── router/          # 路由定义 + 守卫（requiresAuth / requiresAdmin）
│           ├── stores/          # Pinia 状态（auth / segment / history / admin / system）
│           ├── utils/           # 工具函数（auth token / format / theme）
│           ├── layout/          # 布局组件
│           └── views/           # 页面（Home / Segment / History / Profile / Admin / Login）
├── backend/
│   ├── app/
│   │   ├── core/                # 配置 / 数据库 / 异常 / 日志 / JWT 安全 / 统一响应
│   │   ├── api/
│   │   │   ├── routers/         # API 路由（auth/segment/history/admin/model/health）
│   │   │   └── deps.py          # 依赖注入（鉴权、角色校验）
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── services/            # 业务逻辑（推理引擎 / 模型注册 / 视频流水线 / 用户 / 历史）
│   │   └── utils/               # 文件上传校验 & 视频可播放性保障
│   ├── models/                  # ONNX 模型文件
│   ├── static/                  # 静态资源（上传文件/结果文件/头像）
│   ├── scripts/                 # 数据库初始化脚本
│   ├── test/                    # 测试体系（GPU 冒烟 / 性能分析 / 运行时诊断）
│   └── requirements.txt
```

## 功能总览

### 🎨 图像分割
- 上传图片 → 模型推理 → 输出分割掩膜图 + 融合叠加图
- Cityscapes 19 类语义标签（道路/行人/车辆/交通标志等）
- 彩色图例展示各类别分割占比
- 推理耗时实时展示

### 🎬 视频分割（同步模式）
- 上传视频 → 逐帧推理 → 输出分割后视频 + 融合视频
- 平均 FPS、推理总耗时展示

### ⚡ 视频分割（二阶段实时模式）
- **第一阶段（Realtime）**：WebSocket 实时推送进度/帧索引/预览帧/实时 FPS
- **第二阶段（Finalize）**：后台调用 ffmpeg 转码生成最终可播视频（libx264 + yuv420p + faststart）
- 状态机驱动：`idle → running → completed/failed`
- 前端自适应预览渲染策略：按帧率动态调节渲染节奏，优先展示最新帧

### 🔐 用户认证与权限
- 用户注册/登录、JWT Token 签发与验证
- 三级路由守卫：公开页 / 需登录 / 需管理员
- Axios 拦截器自动注入 Bearer Token + 401 失效跳转

### 📋 推理历史
- 图像/视频推理记录自动入库
- 分页查询、详情查看、删除
- 支持同步与实时两种处理模式

### ⚙️ 管理后台
- 用户管理：搜索/角色筛选/状态筛选/编辑/密码重置/账号启停
- 全站推理历史查询与审核
- 管理员专属路由保护

### 🔧 模型与分辨率控制
- 支持切换 DeepLabV3+ / BiSeNetV2 模型
- 4 档预设分辨率选择（512×1024 / 384×768 / 320×640 / 256×512）
- 分辨率切换后自动适配推理输入尺寸

### 🎯 视频可播放性保障
- 后端 ffmpeg 转码确保编码兼容性
- 前端可播性探测与回退机制（HEAD 探测 / metadata 校验 / 缓存戳处理 / 多候选 URL 选择）

## 快速开始

### 前置条件

- **MySQL** 5.7+（创建数据库 `segmentation_system`）
- **Node.js** 18+
- **Python** 3.10+
- **NVIDIA GPU + CUDA**（可选，ONNX Runtime 自动降级 CPU）

### 后端

```bash
cd backend

# Python 虚拟环境
py -3.10 -m venv .venv
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_mysql_auth.py --host 127.0.0.1 --port 3306 --user root --password 123456

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```bash
cd frontend/front

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

默认访问地址：
- 前端：`http://localhost:5173`
- 后端 API：`http://127.0.0.1:8000`
- API 文档：`http://127.0.0.1:8000/docs`

### 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_HOST` | MySQL 主机 | `127.0.0.1` |
| `DB_PORT` | MySQL 端口 | `3306` |
| `DB_USER` | MySQL 用户 | `root` |
| `DB_PASSWORD` | MySQL 密码 | `123456` |
| `DB_NAME` | 数据库名称 | `segmentation_system` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `change-this-in-production` |
| `JWT_EXPIRE_MINUTES` | Token 有效期（分钟） | `120` |
| `DEFAULT_MODEL_KEY` | 默认模型 | `bisenetv2` |
| `MAX_UPLOAD_SIZE_MB` | 最大上传大小 | `100` |
| `VIDEO_POSTPROCESS_MODE` | 视频后处理模式 | `realtime_fast` |

## API 概览

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/auth/me` | 获取当前用户 |
| PUT | `/api/auth/me/profile` | 更新资料 |
| PUT | `/api/auth/me/password` | 修改密码 |
| POST | `/api/auth/avatar` | 上传头像 |

### 模型 & 分辨率
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/model/info` | 模型信息 |
| GET | `/api/segment/resolutions` | 分辨率列表 |

### 图像分割
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/segment` | 图像分割（返回原图/掩膜图/融合图 + 分类占比） |

### 视频分割
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/segment/video` | 同步视频分割 |
| POST | `/api/segment/video/realtime` | 创建实时视频分割任务 |
| WS | `/api/segment/video/ws/{task_id}` | WebSocket 实时预览（进度/FPS/预览帧） |
| POST | `/api/segment/video/finalize/{task_id}` | 触发最终视频生成 |
| GET | `/api/segment/video/result/{task_id}` | 查询最终结果 |

### 历史记录
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/history` | 推理历史列表（分页） |
| GET | `/api/history/{id}` | 历史详情 |
| DELETE | `/api/history/{id}` | 删除历史 |

### 管理后台
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/users` | 用户列表 |
| GET | `/api/admin/users/{id}` | 用户详情 |
| PATCH | `/api/admin/users/{id}` | 编辑用户 |
| PUT | `/api/admin/users/{id}/password` | 重置密码 |
| GET | `/api/admin/histories` | 全站历史查询 |
| PATCH | `/api/admin/histories/{id}` | 更新历史 |
| DELETE | `/api/admin/histories/{id}` | 删除历史 |

## 视频二阶段流程

```
用户上传视频
    ↓
POST /api/segment/video/realtime  → 创建任务，返回 task_id + ws_url
    ↓
WS /api/segment/video/ws/{task_id}  ← 接收实时事件：
    ├─ task_started   → 推理开始
    ├─ task_progress  → 帧进度 / FPS / 预览帧
    ├─ task_completed → 实时阶段完成
    └─ task_failed    → 实时阶段失败
    ↓
POST /api/segment/video/finalize/{task_id}  → 触发最终视频生成
    ↓
GET  /api/segment/video/result/{task_id}    ← 轮询直到 finalize_status=completed
    ↓
播放最终 overlay_video_url
```

### WebSocket 事件类型

| 事件 | 说明 |
|------|------|
| `task_snapshot` | 连接时快照（当前状态概览） |
| `task_started` | 推理开始 |
| `task_progress` | 进度推送（帧索引/总帧数/进度百分比/FPS/预览帧 Base64） |
| `task_completed` | 实时推理完成（含 summary） |
| `task_failed` | 实时推理失败 |

## AI 推理设计要点

### 模型推理引擎
- 采用 ONNX Runtime 加载 FP16 优化模型，优先 CUDAExecutionProvider，失败自动回退 CPUExecutionProvider
- Cityscapes 19 类调色板映射，输出彩色分割掩膜图与半透明融合叠加图

### 视频流水线
- 同步模式：单次请求完成全视频推理与输出
- 二阶段模式：将"实时反馈"与"最终可播放产物"解耦，前者强调响应速度，后者强调编码兼容性

### 视频可播放性保障
- ffmpeg 转码：libx264 + yuv420p + faststart 确保浏览器兼容
- OpenCV 基本可读校验 + 编码检查（要求 h264/avc1）

### 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

- 成功：`code=0`
- 业务异常：`AppException`，`code` 默认为 `1001`

### 日志与请求追踪
- 每个请求注入 X-Request-ID
- 请求级日志：method / path / status / elapsed
- 上传过大、异常堆栈、任务失败有单独 warning/error 日志
