<template>
  <el-card shadow="never" class="video-card">
    <template #header>
      <div class="header-row">
        <span>视频实时展示</span>
        <el-space>
          <el-tag :type="statusTagType" effect="light">实时: {{ statusText }}</el-tag>
          <el-tag :type="finalizeTagType" effect="light">最终视频: {{ finalizeText }}</el-tag>
          <el-tag type="success" effect="light">实时 FPS: {{ realtimeFpsText }}</el-tag>
        </el-space>
      </div>
    </template>

    <div class="progress-wrap">
      <el-progress :percentage="progress" :stroke-width="16" />
      <p class="progress-text" v-if="totalFrames > 0">{{ frameIndex }} / {{ totalFrames }} 帧</p>
    </div>

    <el-row :gutter="12">
      <el-col :xs="24" :md="12">
        <div class="video-wrap">
          <p>原始视频</p>
          <video v-if="originalVideoUrl" :src="originalVideoUrl" controls autoplay muted loop playsinline preload="auto" />
          <el-empty v-else description="请先上传视频" :image-size="70" />
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="video-wrap">
          <p>分割融合视频</p>
          <video
            v-if="finalizeStatus === 'completed' && overlayVideoUrl"
            ref="overlayVideoRef"
            :key="overlayVideoUrl"
            :src="overlayVideoUrl"
            controls
            autoplay
            muted
            loop
            playsinline
            preload="auto"
          />
          <div v-else-if="isFinalizing" class="finalize-loading">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <p>最终视频正在生成中，请稍候...</p>
          </div>
          <img
            v-else-if="displayPreviewImage"
            :src="displayPreviewImage"
            class="preview-image"
            alt="实时预览帧"
            @load="handlePreviewLoad"
          />
          <el-empty v-else description="暂无分割视频" :image-size="70" />
        </div>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'

const props = defineProps<{
  originalVideoUrl: string
  overlayVideoUrl: string
  realtimeFps: number | null
  progress: number
  frameIndex: number
  totalFrames: number
  previewImage: string
  taskStatus: 'idle' | 'queued' | 'running' | 'completed' | 'failed'
  finalizeStatus: 'idle' | 'queued' | 'running' | 'completed' | 'failed'
}>()

const overlayVideoRef = ref<HTMLVideoElement | null>(null)
const displayPreviewImage = ref('')
const pendingPreviewImage = ref('')
const renderTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const lastRenderAt = ref(0)
const pendingLoadStartedAt = ref(0)
const incomingFpsEma = ref(0)
const decodeCostEma = ref(0)
const targetPreviewFps = ref(24)
const minPreviewFps = ref(10)
const maxPreviewFps = ref(36)
const lastIncomingAt = ref(0)

const realtimeFpsText = computed(() => (props.realtimeFps === null ? '--' : props.realtimeFps.toFixed(1)))
const isFinalizing = computed(() => props.finalizeStatus === 'queued' || props.finalizeStatus === 'running')

const statusText = computed(() => {
  if (props.taskStatus === 'queued') return '排队中'
  if (props.taskStatus === 'running') return '处理中'
  if (props.taskStatus === 'completed') return '已完成'
  if (props.taskStatus === 'failed') return '失败'
  return '未开始'
})

const finalizeText = computed(() => {
  if (props.finalizeStatus === 'queued') return '排队中'
  if (props.finalizeStatus === 'running') return '生成中'
  if (props.finalizeStatus === 'completed') return '已完成'
  if (props.finalizeStatus === 'failed') return '失败'
  return '未开始'
})

const statusTagType = computed(() => {
  if (props.taskStatus === 'completed') return 'success'
  if (props.taskStatus === 'failed') return 'danger'
  if (props.taskStatus === 'running') return 'warning'
  return 'info'
})

const finalizeTagType = computed(() => {
  if (props.finalizeStatus === 'completed') return 'success'
  if (props.finalizeStatus === 'failed') return 'danger'
  if (props.finalizeStatus === 'running' || props.finalizeStatus === 'queued') return 'warning'
  return 'info'
})

const estimateDeviceProfile = () => {
  const nav = navigator as Navigator & { deviceMemory?: number }
  const cores = nav.hardwareConcurrency || 4
  const mem = nav.deviceMemory || 4

  if (cores >= 12 || mem >= 16) {
    return { min: 15, max: 45, initial: 34 }
  }

  if (cores >= 8 || mem >= 8) {
    return { min: 12, max: 36, initial: 30 }
  }

  if (cores >= 4 || mem >= 4) {
    return { min: 10, max: 30, initial: 22 }
  }

  return { min: 8, max: 24, initial: 14 }
}

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value))

const updateIncomingFps = () => {
  const now = performance.now()
  if (lastIncomingAt.value > 0) {
    const dt = now - lastIncomingAt.value
    if (dt > 0) {
      const instant = 1000 / dt
      incomingFpsEma.value = incomingFpsEma.value === 0 ? instant : incomingFpsEma.value * 0.82 + instant * 0.18
    }
  }
  lastIncomingAt.value = now
}

const recomputeTargetFps = () => {
  const incoming = incomingFpsEma.value || targetPreviewFps.value
  const decode = decodeCostEma.value || 0
  let desired = Math.min(maxPreviewFps.value, incoming * 0.92)

  if (decode > 48) {
    desired *= 0.65
  } else if (decode > 36) {
    desired *= 0.78
  } else if (decode > 26) {
    desired *= 0.88
  } else if (decode < 14 && incoming > targetPreviewFps.value) {
    desired *= 1.08
  }

  desired = clamp(desired, minPreviewFps.value, maxPreviewFps.value)
  targetPreviewFps.value = targetPreviewFps.value * 0.78 + desired * 0.22
}

const schedulePreviewRender = () => {
  if (renderTimer.value || !pendingPreviewImage.value || props.finalizeStatus === 'completed') {
    return
  }

  const now = performance.now()
  const minInterval = 1000 / Math.max(1, targetPreviewFps.value)
  const elapsed = now - lastRenderAt.value
  const waitMs = Math.max(0, minInterval - elapsed)

  renderTimer.value = setTimeout(() => {
    renderTimer.value = null

    if (!pendingPreviewImage.value || props.finalizeStatus === 'completed') {
      return
    }

    pendingLoadStartedAt.value = performance.now()
    displayPreviewImage.value = pendingPreviewImage.value
    pendingPreviewImage.value = ''
    lastRenderAt.value = performance.now()

    if (pendingPreviewImage.value) {
      schedulePreviewRender()
    }
  }, waitMs)
}

const handlePreviewLoad = () => {
  if (!pendingLoadStartedAt.value) return
  const cost = performance.now() - pendingLoadStartedAt.value
  pendingLoadStartedAt.value = 0
  decodeCostEma.value = decodeCostEma.value === 0 ? cost : decodeCostEma.value * 0.8 + cost * 0.2
  recomputeTargetFps()
  if (pendingPreviewImage.value) {
    schedulePreviewRender()
  }
}

const resetPreviewPipeline = () => {
  if (renderTimer.value) {
    clearTimeout(renderTimer.value)
    renderTimer.value = null
  }
  pendingPreviewImage.value = ''
  displayPreviewImage.value = ''
  lastRenderAt.value = 0
  pendingLoadStartedAt.value = 0
  incomingFpsEma.value = 0
  decodeCostEma.value = 0
  lastIncomingAt.value = 0
}

watch(
  () => props.overlayVideoUrl,
  async (url) => {
    if (!url) return
    await nextTick()
    const video = overlayVideoRef.value
    if (!video) return
    video.load()
    try {
      await video.play()
    } catch {
      // autoplay might be blocked by browser policy; controls are still available.
    }
  },
)

watch(
  () => props.previewImage,
  (img) => {
    if (!img || props.finalizeStatus === 'completed') {
      return
    }
    updateIncomingFps()
    recomputeTargetFps()
    pendingPreviewImage.value = img
    schedulePreviewRender()
  },
)

watch(
  () => props.finalizeStatus,
  (status) => {
    if (status === 'completed') {
      resetPreviewPipeline()
    }
  },
)

const profile = estimateDeviceProfile()
minPreviewFps.value = profile.min
maxPreviewFps.value = profile.max
targetPreviewFps.value = profile.initial

onBeforeUnmount(() => {
  resetPreviewPipeline()
})
</script>

<style scoped>
.video-card {
  height: 100%;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  color: var(--card-header-color);
}

.progress-wrap {
  margin-bottom: 12px;
}

.progress-text {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

.video-wrap {
  border: 1px solid var(--table-border-color);
  border-radius: 8px;
  padding: 10px;
  background: var(--input-surface);
  min-height: 260px;
}

.video-wrap p {
  margin: 0 0 8px;
  color: var(--color-text-deep);
  font-size: 14px;
}

.video-wrap video,
.preview-image {
  width: 100%;
  border-radius: 6px;
  background: #0f1724;
}

.preview-image {
  display: block;
  object-fit: contain;
}

.finalize-loading {
  min-height: 210px;
  border-radius: 8px;
  background: var(--upload-dragger-bg);
  border: 1px dashed var(--upload-dragger-border);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--color-text-muted);
}

.loading-icon {
  font-size: 28px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
