<template>
  <div class="home-view">
    <section class="hero">
      <div class="hero-video-wrap">
        <video
          autoplay
          muted
          loop
          playsinline
          poster="https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&q=80&w=2070"
        >
          <source src="https://cdn.pixabay.com/video/2021/08/04/83897-584705572_large.mp4" type="video/mp4" />
        </video>
      </div>
      <div class="hero-overlay" />
      <div class="hero-overlay-gradient" />

      <div class="hero-content">
        <div class="hero-badge">
          <span class="hero-badge-dot" />
          实时语义分割 · 毫秒级推理
        </div>

        <h1>自动驾驶图像语义分割系统</h1>

        <div class="carousel-container">
          <div
            v-for="(line, index) in carouselLines"
            :key="line"
            class="carousel-line"
            :class="{ active: activeLineIndex === index }"
          >
            {{ line }}
          </div>
        </div>

        <p class="hero-desc">
          构建在先进卷积神经网络架构之上，提供高精度与高帧率道路场景语义分割能力，
          为自动驾驶视觉感知提供稳定、可扩展的工程化体验。
        </p>

        <div class="hero-actions">
          <el-button type="primary" size="large" class="ripple-btn" @click="goSegment">立即体验系统</el-button>
          <el-button size="large" class="ghost-btn ripple-btn" @click="showFeatureModal = true">查看配置面板</el-button>
        </div>
      </div>
    </section>

    <section class="feature-section">
      <div class="feature-inner">
        <h2 class="section-title">核心能力一览</h2>
        <el-row :gutter="20">
          <el-col :xs="24" :md="8">
            <el-card shadow="never" class="feature-card">
              <h3>模型自由切换</h3>
              <p>在 DeepLabV3+ 与 BiSeNetV2 之间平滑切换，兼顾精度与速度。</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-card shadow="never" class="feature-card">
              <h3>实时视频处理</h3>
              <p>支持实时预览 + 最终视频生成双阶段链路，持续反馈 FPS 与进度。</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-card shadow="never" class="feature-card">
              <h3>安全权限体系</h3>
              <p>已接入 JWT、账号隔离、管理员治理能力，保障推理历史可审计可控。</p>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </section>

    <el-dialog v-model="showFeatureModal" title="全局推理配置说明" width="560px">
      <p class="dialog-text">
        当前系统已接入模型切换、实时视频分割、历史记录与权限管理。你可以从顶部导航进入
        图像分割、推理历史、个人主页和管理后台（管理员可见）。
      </p>
      <template #footer>
        <el-button class="ripple-btn" @click="showFeatureModal = false">我知道了</el-button>
        <el-button type="primary" class="ripple-btn" @click="goSegment">去分割工作台</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showFeatureModal = ref(false)
const activeLineIndex = ref(0)
const carouselLines = [
  '上传自动驾驶场景图片并发起分割推理',
  '支持切换 DeepLabV3+ ResNet50 与 BiSeNetV2',
  '已接入登录鉴权与用户隔离的推理历史记录',
  '支持实时视频预览与最终结果双阶段生成',
]

let carouselTimer: ReturnType<typeof setInterval> | null = null

const goSegment = () => {
  void router.push('/segment')
}

onMounted(() => {
  carouselTimer = setInterval(() => {
    activeLineIndex.value = (activeLineIndex.value + 1) % carouselLines.length
  }, 3200)
})

onBeforeUnmount(() => {
  if (carouselTimer) {
    clearInterval(carouselTimer)
    carouselTimer = null
  }
})
</script>

<style scoped>
.home-view {
  width: 100%;
}

.hero {
  position: relative;
  min-height: calc(100vh - 74px);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.hero-video-wrap {
  position: absolute;
  inset: 0;
  z-index: 1;
}

.hero-video-wrap video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: linear-gradient(180deg, rgba(14, 34, 56, 0.42) 0%, rgba(14, 34, 56, 0.78) 65%, rgba(14, 34, 56, 0.92) 100%);
}

.hero-overlay-gradient {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: linear-gradient(125deg, rgba(77, 163, 255, 0.14) 0%, rgba(255, 209, 102, 0.1) 100%);
}

.hero-content {
  position: relative;
  z-index: 3;
  max-width: 1040px;
  text-align: center;
  padding: 0 26px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 18px;
  padding: 8px 18px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.42);
  color: #fff;
  font-size: 13px;
  backdrop-filter: blur(8px);
}

.hero-badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ffd166;
  box-shadow: 0 0 10px rgba(255, 209, 102, 0.85);
}

.hero-content h1 {
  margin: 0;
  font-size: clamp(34px, 5vw, 62px);
  line-height: 1.14;
  color: #fff;
  letter-spacing: -0.02em;
  text-shadow: 0 6px 28px rgba(0, 0, 0, 0.36);
}

.carousel-container {
  margin-top: 24px;
  height: 46px;
  position: relative;
  overflow: hidden;
}

.carousel-line {
  position: absolute;
  inset: 0;
  opacity: 0;
  transform: translateY(18px);
  filter: blur(8px);
  color: rgba(255, 255, 255, 0.95);
  font-size: clamp(18px, 2.2vw, 30px);
  font-weight: 500;
  transition: opacity 0.7s ease, transform 0.7s cubic-bezier(0.21, 1.02, 0.73, 1), filter 0.7s ease;
}

.carousel-line.active {
  opacity: 1;
  transform: translateY(0);
  filter: blur(0);
}

.hero-desc {
  margin: 26px auto 0;
  max-width: 840px;
  font-size: clamp(14px, 1.8vw, 18px);
  color: rgba(255, 255, 255, 0.86);
  line-height: 1.8;
}

.hero-actions {
  margin-top: 38px;
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}

.ghost-btn {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.54) !important;
  background: rgba(255, 255, 255, 0.12) !important;
  backdrop-filter: blur(8px);
}

.ghost-btn:hover {
  color: #ffd166;
  border-color: rgba(255, 209, 102, 0.65) !important;
  background: rgba(255, 255, 255, 0.2) !important;
}

.feature-section {
  position: relative;
  z-index: 4;
  margin-top: -58px;
  padding: 0 20px 44px;
}

.feature-inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 26px;
  border-radius: 26px;
  background: color-mix(in srgb, var(--page-header-bg) 90%, transparent);
  border: 1px solid var(--page-header-border);
  backdrop-filter: blur(12px);
  box-shadow: var(--shadow-md);
}

.section-title {
  margin: 0 0 18px;
  color: var(--page-title-color);
  font-size: 30px;
  text-align: center;
}

.feature-card h3 {
  margin: 0 0 10px;
  color: var(--color-text-deep);
}

.feature-card p {
  margin: 0;
  color: var(--color-text-muted);
  line-height: 1.75;
}

.dialog-text {
  margin: 0;
  color: var(--page-desc-color);
  line-height: 1.8;
}

@media (max-width: 900px) {
  .hero {
    min-height: calc(100vh - 74px);
  }

  .feature-inner {
    padding: 20px;
  }
}
</style>
