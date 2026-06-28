# 自动驾驶图像语义分割系统（前端）
## 1. 项目定位

> 基于 **Vue 3 + Vite + TypeScript + Pinia + Vue Router + Axios + Element Plus** 的演示前端。  
> 支持图像分割、视频实时预览、模型切换、分辨率切换。

---

## 2. 技术栈与版本

`package.json` 当前依赖版本：

- `vue`: `^3.5.30`
- `vue-router`: `^5.0.3`
- `pinia`: `^3.0.4`
- `axios`: `^1.13.6`
- `element-plus`: `^2.13.5`
- `vite`: `^8.0.0`
- `typescript`: `~5.9.3`
- `vue-tsc`: `^3.2.5`

---

## 3. 快速启动

### 3.1 安装依赖

```bash
npm install
```

### 3.2 启动开发环境

```bash
npm run dev
```

默认前端地址通常是：`http://127.0.0.1:5173`

### 3.3 打包构建

```bash
npm run build
```

### 3.4 本地预览构建产物

```bash
npm run preview
```

---

## 4. 后端联调与代理

开发环境通过 `vite.config.ts` 代理：

- `/api` -> `http://127.0.0.1:8000`（`ws: true`，支持 WebSocket）
- `/static` -> `http://127.0.0.1:8000`

这意味着：

- 开发时前端请求可直接写相对路径（例如 `/api/segment`）。
- 静态资源 `/static/result/...` 会被代理到 FastAPI。

---

## 5. 环境变量说明

请求层文件：`src/api/request.ts`

Axios 默认配置：

- `baseURL = import.meta.env.VITE_API_BASE_URL ?? '/'`
- `timeout = 15000`

可选环境变量：

- `VITE_API_BASE_URL`：覆盖默认 API 基地址。
- `VITE_FILE_BASE_URL`：用于拼接静态资源地址（`resolveAssetUrl`）。

如果未配置上述变量，开发环境通常依赖 Vite 代理即可。

---

## 6. 目录结构（核心）

```text
front/
├─ public/
│  ├─ favicon.svg
│  └─ icons.svg
├─ src/
│  ├─ api/
│  │  ├─ modules/
│  │  │  ├─ model.ts
│  │  │  └─ segment.ts
│  │  ├─ index.ts
│  │  ├─ mock.ts
│  │  ├─ request.ts
│  │  └─ types.ts
│  ├─ assets/
│  │  └─ hero.png
│  ├─ components/
│  │  ├─ ClassLegend.vue
│  │  ├─ InferenceInfoPanel.vue
│  │  ├─ ModelSelector.vue
│  │  ├─ PageContainer.vue
│  │  ├─ ResultDisplay.vue
│  │  ├─ TopNav.vue
│  │  ├─ UploadPanel.vue
│  │  └─ VideoResultPanel.vue
│  ├─ layout/
│  │  └─ MainLayout.vue
│  ├─ router/
│  │  └─ index.ts
│  ├─ stores/
│  │  ├─ segment.ts
│  │  └─ system.ts
│  ├─ utils/
│  │  └─ format.ts
│  ├─ views/
│  │  ├─ AboutView.vue
│  │  ├─ HomeView.vue
│  │  └─ SegmentView.vue
│  ├─ App.vue
│  ├─ main.ts
│  └─ style.css
├─ index.html
├─ package.json
├─ tsconfig*.json
└─ vite.config.ts
```

---

## 7. 页面与路由

路由配置在 `src/router/index.ts`：

- `/`：系统介绍页（`HomeView`）
- `/segment`：分割工作台（图像 + 视频）（`SegmentView`）
- `/about`：关于系统页（`AboutView`）

页面标题会在 `afterEach` 中自动更新。

---

## 8. 全局状态（Pinia）

### 8.1 `system` store（`src/stores/system.ts`）

负责：

- 系统标题与副标题。
- 模型选项（DeepLabV3+ / BiSeNetV2）。
- 当前选中模型 `selectedModelKey`。
- 模型信息拉取（`/api/model/info`）。

### 8.2 `segment` store（`src/stores/segment.ts`）

负责：

- 图像与视频文件、预览、分割结果。
- 分辨率选项拉取与当前选择（图片/视频分别独立）。
- 视频实时状态（realtime）与最终生成状态（finalize）分离管理。
- 实时进度、帧索引、总帧数、实时 FPS、预览帧 Base64。

关键状态字段（视频相关）：

- `videoRealtimeStatus`: `idle | queued | running | completed | failed`
- `videoFinalizeStatus`: `idle | queued | running | completed | failed`
- `videoSummary`: 实时阶段汇总（帧数、平均/实时 FPS、耗时等）
- `videoResult`: 最终视频结果（含 overlay URL）
- `videoPreviewBase64`: 实时预览帧

---

## 9. API 请求层

### 9.1 统一响应结构

前端按统一格式解析：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

Axios 拦截器规则：

- `code !== 0` 视为业务异常并抛错。
- 网络/HTTP 异常统一转成可展示错误信息。

### 9.2 已对接接口清单

模型信息：

- `GET /api/model/info?model_key=...`

分辨率选项：

- `GET /api/segment/resolutions`

图像分割：

- `POST /api/segment`
- `form-data`: `file`, `model_key`, `resolution?`

视频分割（同步）：

- `POST /api/segment/video`
- `form-data`: `file`, `model_key`, `resolution?`

视频分割（实时阶段）：

- `POST /api/segment/video/realtime`
- `form-data`: `file`, `model_key`, `resolution?`

视频最终生成触发：

- `POST /api/segment/video/finalize/{task_id}`

视频最终结果查询：

- `GET /api/segment/video/result/{task_id}`

WebSocket：

- `WS /api/segment/video/ws/{task_id}`

---

## 10. 视频二阶段状态机（当前实现）

位置：`src/views/SegmentView.vue`

### 10.1 流程

1. 上传视频并调用 `POST /api/segment/video/realtime`。
2. 根据返回 `ws_url` 建立 WebSocket 连接。
3. 接收实时事件：进度、实时 FPS、预览帧。
4. 收到实时阶段 `task_completed` 后自动触发 `POST /finalize/{task_id}`。
5. 进入 `finalize_status=queued/running`，前端轮询 `GET /result/{task_id}`。
6. `finalize_status=completed` 后获取最终 `result.overlay_video_url` 并播放。

### 10.2 WS 事件（前端已处理）

- `task_snapshot`
- `task_started`
- `task_progress`
- `task_completed`（实时阶段完成）
- `task_finalize_started`
- `task_finalize_completed`
- `task_finalize_failed`
- `task_failed`

### 10.3 UI 行为

- 运行中：显示预览帧、进度、实时 FPS。
- finalize 中：在“分割融合视频”区域显示加载图标与“最终视频正在生成中”。
- finalize 完成：切换到最终视频播放器（支持循环播放）。

---

## 11. 自适应预览帧率策略

位置：`src/components/VideoResultPanel.vue`

为减少实时预览闪烁并兼顾性能，预览渲染采用“自适应调度”，而不是固定帧率：

- 根据设备能力（`hardwareConcurrency`、`deviceMemory`）给初始目标 FPS。
- 依据 WS 到帧速率（EMA）和图片解码耗时（EMA）动态调节目标 FPS。
- 始终优先渲染最新帧，防止队列堆积造成卡顿和延迟。

注意：

- 页面显示的“实时 FPS”是后端提供的 `realtime_fps`，不是前端渲染 FPS。
- 前端自适应策略只影响“预览观感”，不直接改变后端推理速度。

---

## 12. 分辨率选择

位置：

- API：`src/api/modules/segment.ts`
- 状态：`src/stores/segment.ts`
- UI：`src/components/UploadPanel.vue`

行为：

- 页面加载时拉取 `/api/segment/resolutions`。
- 图像和视频分别可选择分辨率。
- 发起分割时将 `resolution` 写入 form-data。

后端返回的 `input_size` 会反映本次实际推理分辨率。

---

## 13. 组件职责说明

- `TopNav.vue`：顶部导航与页面切换。
- `ModelSelector.vue`：模型下拉切换。
- `UploadPanel.vue`：上传入口、分辨率选择、启动/重置按钮。
- `ResultDisplay.vue`：图片结果卡片（原图/分割图/融合图）。
- `InferenceInfoPanel.vue`：模型、输入尺寸、耗时、FPS 展示。
- `ClassLegend.vue`：类别颜色与占比表。
- `VideoResultPanel.vue`：视频进度、实时预览、finalize 加载态、最终视频播放。

---

## 14. 常见问题与排查

### 14.1 预览阶段闪烁

已做自适应预览渲染。如仍明显：

- 检查后端推送频率是否过高。
- 检查浏览器扩展是否干扰渲染。
- 观察开发者工具 Performance，定位解码瓶颈。

### 14.2 最终视频黑屏/0:00

前端已做：

- finalize 完成后才加载最终视频。
- 对结果 URL 加缓存戳。
- 播放前可播性探测（metadata）。

若仍黑屏，多数是后端编码兼容问题，建议后端输出：

- `H.264 + yuv420p + faststart`

### 14.3 控制台出现字体慢速或插件报错

- `Slow network ... Roboto`：通常是字体加载提示，不一定是业务错误。
- `Unchecked runtime.lastError ...`：常见于浏览器扩展，不一定来自项目代码。

---

## 15. 开发建议

- 联调优先使用真实后端，不建议长期依赖 mock。
- 新增接口时先在 `src/api/types.ts` 明确结构，再接 API 与 store。
- 视频链路改动请保持“realtime / finalize”双状态分离，避免状态混淆。
- 对 WebSocket 事件建议增加版本号或 schema 约束，降低前后端升级风险。

---

## 16. 许可证与说明

本仓库用于个人项目设计演示与研发验证。  

