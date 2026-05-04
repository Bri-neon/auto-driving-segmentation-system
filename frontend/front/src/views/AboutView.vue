<template>
  <PageContainer
    title="关于系统"
    description="面向毕业设计答辩的系统总览：任务目标、训练与微调流程、模型对比与工程化落地。"
  >
    <el-card shadow="never" class="about-card hero-card">
      <template #header>
        <div class="section-title">项目定位与答辩目标</div>
      </template>
      <div class="hero-grid">
        <div>
          <h3>自动驾驶场景语义分割全链路系统</h3>
          <p>
            本项目聚焦道路场景的像素级语义理解，支持图像与视频两种输入模式，核心目标是将模型训练成果
            完整落地到可交互系统中，形成“训练-导出-推理-历史审计-权限治理”的闭环。
          </p>
          <p>
            系统面向毕业设计答辩场景，强调三个关键词：可解释、可复现、可演示。既展示算法效果，
            也覆盖工程能力与产品化实现。
          </p>
        </div>
        <div class="pillars">
          <div class="pillar-card">
            <h4>算法侧</h4>
            <p>DeepLabV3+（ResNet50 Backbone）训练与微调、指标跟踪、可视化分析。</p>
          </div>
          <div class="pillar-card">
            <h4>工程侧</h4>
            <p>FastAPI + Vue3 全链路联调，JWT 鉴权、历史落库、管理员治理能力。</p>
          </div>
          <div class="pillar-card">
            <h4>展示侧</h4>
            <p>实时视频预览 + 最终视频生成双阶段展示，支持模型切换与结果回放对比。</p>
          </div>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="section-row">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="about-card">
          <template #header>
            <div class="section-title">训练与微调过程（基于真实记录）</div>
          </template>
          <ul class="timeline-list">
            <li>
              <span class="timeline-tag">Baseline 训练</span>
              基于 Cityscapes 数据集训练 DeepLabV3+，`max_iters=40000`，`val_interval=2000`。
            </li>
            <li>
              <span class="timeline-tag">微调起点</span>
              使用 `iter_36000.pth` 作为微调初始化权重，保持主干能力并加速收敛。
            </li>
            <li>
              <span class="timeline-tag">Finetune 配置</span>
              微调阶段 `max_iters=8000`，`val_interval=1000`，更高频验证以观察提升趋势。
            </li>
            <li>
              <span class="timeline-tag">最佳指标</span>
              在 `8000 iter` 达到最佳：`mIoU 79.18`、`mAcc 86.60`、`aAcc 96.25`。
            </li>
          </ul>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="about-card">
          <template #header>
            <div class="section-title">模型关系与使用策略</div>
          </template>
          <div class="model-note">
            <h4>DeepLabV3+ 与 ResNet50 的关系</h4>
            <p>
              DeepLabV3+ 是语义分割框架，ResNet50 是其主干特征提取网络（Backbone）。
              在本系统中，“DeepLabV3+ ResNet50”表示二者组合后的完整模型。
            </p>
            <h4>BiSeNetV2 的使用说明</h4>
            <p>
              BiSeNetV2 在当前版本中主要用于工程侧实时对比演示，采用公开可用权重进行推理部署，
              重点体现与 DeepLabV3+ 的速度/精度取舍差异。
            </p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="section-row">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="about-card">
          <template #header>
            <div class="section-title">对比图 1：微调阶段 mIoU 提升曲线（真实日志点）</div>
          </template>

          <div class="chart-wrap">
            <svg viewBox="0 0 760 280" class="line-chart" role="img" aria-label="微调mIoU曲线">
              <line x1="60" y1="20" x2="60" y2="240" class="axis-line" />
              <line x1="60" y1="240" x2="730" y2="240" class="axis-line" />

              <line v-for="tick in yTicks" :key="`y-${tick}`" :x1="60" :y1="toY(tick)" :x2="730" :y2="toY(tick)" class="grid-line" />
              <polyline :points="linePoints" class="curve-line" />
              <circle
                v-for="point in finetuneSeries"
                :key="point.iter"
                :cx="toX(point.iter)"
                :cy="toY(point.miou)"
                r="4.5"
                class="curve-dot"
              />
              <text v-for="point in finetuneSeries" :key="`t-${point.iter}`" :x="toX(point.iter) - 20" :y="toY(point.miou) - 10" class="dot-label">
                {{ point.miou.toFixed(2) }}
              </text>

              <text x="330" y="274" class="axis-label">微调迭代步数（iter）</text>
              <text x="16" y="132" class="axis-label" transform="rotate(-90 16 132)">mIoU (%)</text>

              <text v-for="tick in yTicks" :key="`yl-${tick}`" x="20" :y="toY(tick) + 4" class="tick-label">
                {{ tick.toFixed(2) }}
              </text>
              <text v-for="point in finetuneSeries" :key="`xl-${point.iter}`" :x="toX(point.iter) - 14" y="258" class="tick-label">
                {{ point.iter }}
              </text>
            </svg>
          </div>

          <p class="chart-caption">
            说明：该曲线节点来自微调日志关键验证点（1000~8000 iter）。
          </p>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="about-card score-card">
          <template #header>
            <div class="section-title">对比图 2：模型工程定位（演示维度）</div>
          </template>
          <p class="score-note">
            指标说明：下列数值单位为“分”（0-100），用于本系统答辩演示的工程归一化评估分，
            综合了公开资料趋势与当前项目部署体验，不代表官方统一Benchmark分数。
          </p>
          <div class="bars">
            <div v-for="item in comparisonBars" :key="item.name" class="bar-item">
              <div class="bar-title">{{ item.name }}</div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: `${item.value}%` }"></div>
              </div>
              <div class="bar-value">{{ item.value }} 分</div>
            </div>
          </div>

          <div class="legend-note">
            <span class="dot deep"></span> DeepLabV3+ ResNet50：偏精度、模型更重
            <br />
            <span class="dot bi"></span> BiSeNetV2：偏实时、部署更轻
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="about-card section-row">
      <template #header>
        <div class="section-title">对比图 3：模型能力与落地场景对照</div>
      </template>
      <div class="compare-table-wrap">
        <table class="compare-table">
          <thead>
            <tr>
              <th>维度</th>
              <th>DeepLabV3+ ResNet50</th>
              <th>BiSeNetV2</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>核心定位</td>
              <td>精度优先，适合离线评估与高质量结果输出</td>
              <td>速度优先，适合实时预览与轻量演示</td>
            </tr>
            <tr>
              <td>训练来源</td>
              <td>Cityscapes Baseline + Finetune 实验链路</td>
              <td>公开可用权重用于部署对比</td>
            </tr>
            <tr>
              <td>部署特征</td>
              <td>推理开销较高，换取更稳健语义边界</td>
              <td>推理开销较低，响应速度更友好</td>
            </tr>
            <tr>
              <td>答辩展示建议</td>
              <td>展示精细分割效果、类别边界与日志指标提升</td>
              <td>展示实时性、帧率与交互响应能力</td>
            </tr>
          </tbody>
        </table>
      </div>
    </el-card>

    <el-row :gutter="16" class="section-row">
      <el-col :xs="24" :md="24">
        <el-card shadow="never" class="about-card">
          <template #header>
            <div class="section-title">工程技术栈</div>
          </template>
          <ul class="plain-list">
            <li>前端：Vue 3 + Vite + TypeScript + Element Plus</li>
            <li>路由与状态：Vue Router + Pinia</li>
            <li>请求层：Axios + JWT 鉴权拦截</li>
            <li>后端：FastAPI + ONNX Runtime + MySQL</li>
            <li>能力：权限分级、历史审计、实时任务与最终视频双阶段</li>
          </ul>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="section-row">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="about-card">
          <template #header>
            <div class="section-title">六维雷达对比（演示评分）</div>
          </template>
          <div class="radar-panel">
            <svg viewBox="0 0 420 320" class="radar-svg" role="img" aria-label="DeepLabV3+、BiSeNetV2、SAM3六维雷达图">
              <polygon
                v-for="level in radarLevels"
                :key="`g-${level}`"
                :points="radarGridPoints(level)"
                class="radar-grid"
              />
              <line
                v-for="(metric, idx) in radarMetrics"
                :key="`a-${metric.label}`"
                :x1="radarCenter.x"
                :y1="radarCenter.y"
                :x2="radarAxisPoint(idx, 1).x"
                :y2="radarAxisPoint(idx, 1).y"
                class="radar-axis"
              />

              <polygon :points="deeplabPolygon" class="radar-deeplab" />
              <polygon :points="bisenetPolygon" class="radar-bisenet" />
              <polygon :points="sam3Polygon" class="radar-sam" />

              <text
                v-for="(metric, idx) in radarMetrics"
                :key="`l-${metric.label}`"
                :x="radarAxisPoint(idx, 1.12).x"
                :y="radarAxisPoint(idx, 1.12).y"
                class="radar-label"
              >
                {{ metric.label }}
              </text>
            </svg>
            <div class="radar-legend">
              <span><i class="chip deep"></i> DeepLabV3+ ResNet50</span>
              <span><i class="chip bi"></i> BiSeNetV2</span>
              <span><i class="chip sam"></i> SAM3</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="about-card arch-card">
          <template #header>
            <div class="section-title">系统架构图（前端-后端-数据库）</div>
          </template>
          <svg viewBox="0 0 640 360" class="arch-svg" role="img" aria-label="系统架构图">
            <defs>
              <marker id="arrowEnd" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                <path d="M0,0 L8,4 L0,8 Z" class="arch-arrow-head" />
              </marker>
            </defs>

            <rect x="26" y="130" width="140" height="68" rx="12" class="arch-node front" />
            <text x="96" y="158" class="arch-node-title">Vue Frontend</text>
            <text x="96" y="178" class="arch-node-sub">Web UI / Router / Pinia</text>

            <rect x="228" y="72" width="170" height="62" rx="12" class="arch-node mid" />
            <text x="313" y="100" class="arch-node-title">FastAPI API Layer</text>
            <text x="313" y="120" class="arch-node-sub">Auth / History / Segment</text>

            <rect x="228" y="216" width="170" height="62" rx="12" class="arch-node mid" />
            <text x="313" y="244" class="arch-node-title">Inference Services</text>
            <text x="313" y="264" class="arch-node-sub">ONNX Runtime / Realtime</text>

            <rect x="470" y="62" width="146" height="62" rx="12" class="arch-node data" />
            <text x="543" y="90" class="arch-node-title">MySQL</text>
            <text x="543" y="110" class="arch-node-sub">users / histories</text>

            <rect x="470" y="222" width="146" height="62" rx="12" class="arch-node data" />
            <text x="543" y="250" class="arch-node-title">Static Storage</text>
            <text x="543" y="270" class="arch-node-sub">upload / result / avatar</text>

            <line x1="166" y1="164" x2="228" y2="103" class="arch-link" marker-end="url(#arrowEnd)" />
            <line x1="166" y1="164" x2="228" y2="247" class="arch-link" marker-end="url(#arrowEnd)" />

            <line x1="398" y1="103" x2="470" y2="93" class="arch-link" marker-end="url(#arrowEnd)" />
            <line x1="398" y1="247" x2="470" y2="253" class="arch-link" marker-end="url(#arrowEnd)" />

            <line x1="313" y1="134" x2="313" y2="216" class="arch-link dashed" marker-end="url(#arrowEnd)" />

            <text x="192" y="142" class="arch-note">HTTP / WS</text>
            <text x="430" y="82" class="arch-note">ORM / SQL</text>
            <text x="421" y="236" class="arch-note">File URL</text>
          </svg>
        </el-card>
      </el-col>
    </el-row>
  </PageContainer>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import PageContainer from '../components/PageContainer.vue'

type MiouPoint = {
  iter: number
  miou: number
}

const finetuneSeries: MiouPoint[] = [
  { iter: 1000, miou: 78.37 },
  { iter: 2000, miou: 78.54 },
  { iter: 3000, miou: 78.82 },
  { iter: 4000, miou: 78.93 },
  { iter: 5000, miou: 78.95 },
  { iter: 7000, miou: 79.15 },
  { iter: 8000, miou: 79.18 },
]

const yTicks = [78.2, 78.4, 78.6, 78.8, 79.0, 79.2]

const minIter = finetuneSeries[0].iter
const maxIter = finetuneSeries[finetuneSeries.length - 1].iter
const minMiou = yTicks[0]
const maxMiou = yTicks[yTicks.length - 1]

const toX = (iter: number) => {
  const left = 60
  const right = 730
  return left + ((iter - minIter) / (maxIter - minIter)) * (right - left)
}

const toY = (miou: number) => {
  const top = 20
  const bottom = 240
  return bottom - ((miou - minMiou) / (maxMiou - minMiou)) * (bottom - top)
}

const linePoints = computed(() => finetuneSeries.map((p) => `${toX(p.iter)},${toY(p.miou)}`).join(' '))

const comparisonBars = [
  { name: 'DeepLabV3+ 精度导向', value: 88 },
  { name: 'DeepLabV3+ 实时导向', value: 58 },
  { name: 'BiSeNetV2 精度导向', value: 76 },
  { name: 'BiSeNetV2 实时导向', value: 92 },
]

type RadarMetric = {
  label: string
  deeplab: number
  bisenet: number
  sam3: number
}

const radarMetrics: RadarMetric[] = [
  { label: '分割精度', deeplab: 86, bisenet: 74, sam3: 95 },
  { label: '实时性能', deeplab: 58, bisenet: 89, sam3: 18 },
  { label: '显存友好度', deeplab: 56, bisenet: 82, sam3: 22 },
  { label: '部署轻量度', deeplab: 54, bisenet: 84, sam3: 30 },
  { label: '边界细节', deeplab: 88, bisenet: 70, sam3: 94 },
  { label: '场景泛化', deeplab: 80, bisenet: 72, sam3: 90 },
]

const radarCenter = { x: 170, y: 150 }
const radarRadius = 112
const radarLevels = [0.2, 0.4, 0.6, 0.8, 1]

const radarAxisPoint = (index: number, ratio: number) => {
  const angle = ((-90 + (360 / radarMetrics.length) * index) * Math.PI) / 180
  return {
    x: radarCenter.x + Math.cos(angle) * radarRadius * ratio,
    y: radarCenter.y + Math.sin(angle) * radarRadius * ratio,
  }
}

const radarGridPoints = (ratio: number) =>
  radarMetrics
    .map((_, idx) => {
      const point = radarAxisPoint(idx, ratio)
      return `${point.x},${point.y}`
    })
    .join(' ')

const buildRadarPolygon = (model: 'deeplab' | 'bisenet' | 'sam3') =>
  radarMetrics
    .map((metric, idx) => {
      const score =
        (model === 'deeplab' ? metric.deeplab : model === 'bisenet' ? metric.bisenet : metric.sam3) / 100
      const point = radarAxisPoint(idx, score)
      return `${point.x},${point.y}`
    })
    .join(' ')

const deeplabPolygon = computed(() => buildRadarPolygon('deeplab'))
const bisenetPolygon = computed(() => buildRadarPolygon('bisenet'))
const sam3Polygon = computed(() => buildRadarPolygon('sam3'))
</script>

<style scoped>
.about-card {
  height: 100%;
}

.section-title {
  font-weight: 700;
  color: var(--card-header-color);
}

.section-row {
  margin-top: 16px;
}

.hero-card h3 {
  margin: 0 0 8px;
  font-size: 22px;
  color: var(--color-text-deep);
}

.hero-card p {
  margin: 0 0 12px;
  color: var(--page-desc-color);
  line-height: 1.75;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
}

.pillars {
  display: grid;
  gap: 12px;
}

.pillar-card {
  border: 1px solid var(--table-border-color);
  background: var(--input-surface);
  border-radius: 12px;
  padding: 12px;
}

.pillar-card h4 {
  margin: 0 0 6px;
  color: var(--color-text-deep);
}

.pillar-card p {
  margin: 0;
}

.timeline-list,
.plain-list {
  margin: 0;
  padding-left: 20px;
  color: var(--page-desc-color);
  line-height: 1.9;
}

.timeline-list li {
  margin-bottom: 8px;
}

.timeline-tag {
  display: inline-block;
  margin-right: 8px;
  padding: 2px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-accent-blue) 18%, transparent);
  color: var(--color-accent-blue);
  font-size: 12px;
  font-weight: 700;
}

.model-note h4 {
  margin: 0 0 8px;
  color: var(--color-text-deep);
}

.model-note p {
  margin: 0 0 14px;
  color: var(--page-desc-color);
  line-height: 1.8;
}

.chart-wrap {
  border: 1px solid var(--table-border-color);
  border-radius: 12px;
  padding: 10px;
  background: var(--input-surface);
}

.line-chart {
  width: 100%;
  height: auto;
  display: block;
}

.axis-line {
  stroke: var(--color-text-muted);
  stroke-width: 1.4;
}

.grid-line {
  stroke: color-mix(in srgb, var(--table-border-color) 75%, transparent);
  stroke-dasharray: 5 5;
  stroke-width: 1;
}

.curve-line {
  fill: none;
  stroke: var(--color-accent-blue);
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.curve-dot {
  fill: var(--color-accent-yellow);
  stroke: var(--color-accent-blue);
  stroke-width: 2;
}

.dot-label {
  font-size: 12px;
  fill: var(--color-text-deep);
  font-weight: 600;
}

.axis-label {
  font-size: 13px;
  fill: var(--color-text-muted);
}

.tick-label {
  font-size: 12px;
  fill: var(--color-text-muted);
}

.chart-caption {
  margin: 10px 2px 0;
  color: var(--color-text-muted);
  font-size: 13px;
}

.score-note {
  margin: 0 0 14px;
  font-size: 12px;
  line-height: 1.7;
  color: var(--color-text-muted);
}

.bars {
  display: grid;
  gap: 12px;
}

.bar-item {
  display: grid;
  grid-template-columns: 1fr 2.2fr 44px;
  gap: 10px;
  align-items: center;
}

.bar-title {
  color: var(--color-text-deep);
  font-size: 13px;
}

.bar-track {
  height: 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--table-border-color) 65%, transparent);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--color-accent-blue), var(--color-accent-yellow));
}

.bar-value {
  text-align: right;
  color: var(--color-text-muted);
  font-size: 12px;
}

.legend-note {
  margin-top: 14px;
  font-size: 13px;
  color: var(--color-text-muted);
  line-height: 1.8;
}

.score-card :deep(.el-card__body) {
  min-height: 454px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
}

.dot.deep {
  background: var(--color-accent-blue);
}

.dot.bi {
  background: var(--color-accent-yellow);
}

.compare-table-wrap {
  overflow-x: auto;
}

.compare-table {
  width: 100%;
  border-collapse: collapse;
  border-radius: 10px;
  overflow: hidden;
}

.compare-table th,
.compare-table td {
  border: 1px solid var(--table-border-color);
  padding: 12px 10px;
  text-align: left;
  line-height: 1.7;
}

.compare-table th {
  background: var(--input-surface);
  color: var(--color-text-deep);
}

.compare-table td {
  color: var(--page-desc-color);
}

.radar-panel {
  border: 1px solid var(--table-border-color);
  border-radius: 12px;
  background: var(--input-surface);
  padding: 12px;
  min-height: 360px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.radar-svg {
  width: 100%;
  height: auto;
  display: block;
}

.radar-grid {
  fill: none;
  stroke: color-mix(in srgb, var(--table-border-color) 75%, transparent);
  stroke-width: 1;
}

.radar-axis {
  stroke: color-mix(in srgb, var(--color-text-muted) 60%, transparent);
  stroke-width: 1;
}

.radar-deeplab {
  fill: color-mix(in srgb, var(--color-accent-blue) 24%, transparent);
  stroke: var(--color-accent-blue);
  stroke-width: 2;
}

.radar-bisenet {
  fill: color-mix(in srgb, var(--color-accent-yellow) 22%, transparent);
  stroke: var(--color-accent-yellow);
  stroke-width: 2;
}

.radar-sam {
  fill: color-mix(in srgb, #6ccf8a 20%, transparent);
  stroke: #6ccf8a;
  stroke-width: 2;
}

.radar-label {
  font-size: 12px;
  fill: var(--color-text-muted);
  text-anchor: middle;
}

.radar-legend {
  display: flex;
  gap: 18px;
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.chip {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
}

.chip.deep {
  background: var(--color-accent-blue);
}

.chip.bi {
  background: var(--color-accent-yellow);
}

.chip.sam {
  background: #6ccf8a;
}

.arch-card :deep(.el-card__body) {
  min-height: 360px;
  display: flex;
  align-items: center;
}

.arch-svg {
  width: 100%;
  height: auto;
  display: block;
}

.arch-node {
  stroke: color-mix(in srgb, var(--table-border-color) 85%, transparent);
  stroke-width: 1.2;
}

.arch-node.front {
  fill: color-mix(in srgb, var(--color-accent-blue) 24%, #ffffff);
}

.arch-node.mid {
  fill: color-mix(in srgb, var(--color-accent-yellow) 20%, #ffffff);
}

.arch-node.data {
  fill: color-mix(in srgb, #7cc9a8 26%, #ffffff);
}

.arch-node-title {
  text-anchor: middle;
  font-size: 15px;
  font-weight: 700;
  fill: var(--color-text-deep);
}

.arch-node-sub {
  text-anchor: middle;
  font-size: 12px;
  fill: var(--color-text-muted);
}

.arch-link {
  stroke: color-mix(in srgb, var(--color-text-muted) 75%, transparent);
  stroke-width: 1.7;
  fill: none;
}

.arch-link.dashed {
  stroke-dasharray: 6 5;
}

.arch-arrow-head {
  fill: color-mix(in srgb, var(--color-text-muted) 85%, transparent);
}

.arch-note {
  text-anchor: middle;
  font-size: 12px;
  fill: var(--color-text-muted);
}

@media (max-width: 960px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .score-card :deep(.el-card__body) {
    min-height: auto;
  }

  .arch-card :deep(.el-card__body),
  .radar-panel {
    min-height: auto;
  }
}
</style>
