<template>
  <PageContainer
    title="语义分割工作台"
    description="支持图像与视频的自动驾驶场景语义分割展示，可切换 DeepLabV3+ ResNet50 与 BiSeNetV2 模型。"
  >
    <el-alert
      title="视频分割已升级为二阶段：实时预览完成后将自动生成最终视频。"
      type="success"
      :closable="false"
      show-icon
    />

    <el-row :gutter="16">
      <el-col :xs="24" :lg="8">
        <ModelSelector
          :model-key="systemStore.selectedModelKey"
          :options="systemStore.modelOptions"
          @change="onModelChange"
        />
      </el-col>
      <el-col :xs="24" :lg="16">
        <InferenceInfoPanel
          :model-info="systemStore.modelInfo"
          :model-name="activeModelName"
          :input-size="activeInputSize"
          :inference-time="activeInferenceTime"
          :realtime-fps="activeRealtimeFps"
          :avg-fps="activeAvgFps"
        />
      </el-col>
    </el-row>

    <el-tabs v-model="activeMode" class="mode-tabs">
      <el-tab-pane label="图像分割" name="image">
        <el-row :gutter="16">
          <el-col :xs="24" :lg="8">
            <UploadPanel
              mode="image"
              :loading="segmentStore.imageLoading"
              :has-file="Boolean(segmentStore.imageFile)"
              :selected-resolution="segmentStore.selectedImageResolution"
              :resolution-options="segmentStore.imageResolutionOptions"
              :resolution-loading="segmentStore.resolutionLoading"
              @select="onImageFileSelect"
              @resolution-change="onImageResolutionChange"
              @run="onImageRun"
              @reset="onImageReset"
            />
          </el-col>

          <el-col :xs="24" :lg="16">
            <el-row :gutter="16">
              <el-col :xs="24" :md="8">
                <ResultDisplay title="原图预览" :image-url="imageOriginalUrl" empty-text="请先上传图片" />
              </el-col>
              <el-col :xs="24" :md="8">
                <ResultDisplay title="分割结果图" :image-url="imageSegmentedUrl" empty-text="暂无分割结果" />
              </el-col>
              <el-col :xs="24" :md="8">
                <ResultDisplay title="融合图 (Overlay)" :image-url="imageOverlayUrl" empty-text="暂无融合图" />
              </el-col>
            </el-row>
          </el-col>
        </el-row>

        <ClassLegend :classes="imageClasses" />
      </el-tab-pane>

      <el-tab-pane label="视频分割" name="video">
        <el-row :gutter="16">
          <el-col :xs="24" :lg="8">
            <UploadPanel
              mode="video"
              :loading="segmentStore.videoLoading"
              :has-file="Boolean(segmentStore.videoFile)"
              :selected-resolution="segmentStore.selectedVideoResolution"
              :resolution-options="segmentStore.videoResolutionOptions"
              :resolution-loading="segmentStore.resolutionLoading"
              @select="onVideoFileSelect"
              @resolution-change="onVideoResolutionChange"
              @run="onVideoRun"
              @reset="onVideoReset"
            />
          </el-col>
          <el-col :xs="24" :lg="16">
            <VideoResultPanel
              :original-video-url="videoOriginalUrl"
              :overlay-video-url="videoOverlayUrl"
              :realtime-fps="activeRealtimeFps"
              :progress="segmentStore.videoProgress"
              :frame-index="segmentStore.videoFrameIndex"
              :total-frames="segmentStore.videoTotalFrames"
              :preview-image="videoPreviewImage"
              :task-status="segmentStore.videoRealtimeStatus"
              :finalize-status="segmentStore.videoFinalizeStatus"
            />
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import ClassLegend from '../components/ClassLegend.vue'
import InferenceInfoPanel from '../components/InferenceInfoPanel.vue'
import ModelSelector from '../components/ModelSelector.vue'
import PageContainer from '../components/PageContainer.vue'
import ResultDisplay from '../components/ResultDisplay.vue'
import UploadPanel from '../components/UploadPanel.vue'
import VideoResultPanel from '../components/VideoResultPanel.vue'
import {
  fetchVideoFinalizeResult,
  triggerVideoFinalize,
  type ModelKey,
  type VideoRealtimeEvent,
  type VideoSegmentResult,
} from '../api'
import { useSegmentStore } from '../stores/segment'
import { useSystemStore } from '../stores/system'
import { resolveAssetUrl } from '../utils/format'
import { getAccessToken } from '../utils/auth'

const systemStore = useSystemStore()
const segmentStore = useSegmentStore()

const activeMode = ref<'image' | 'video'>('image')
const wsRef = ref<WebSocket | null>(null)
const finalPlayableVideoUrl = ref('')
let resultPollTimer: ReturnType<typeof setInterval> | null = null
let pollingBusy = false
let finalizingRequestedTaskId = ''

const imageOriginalUrl = computed(() => {
  return resolveAssetUrl(segmentStore.imageResult?.original_image_url || segmentStore.imagePreviewUrl)
})

const imageSegmentedUrl = computed(() => resolveAssetUrl(segmentStore.imageResult?.segmented_image_url || ''))
const imageOverlayUrl = computed(() => resolveAssetUrl(segmentStore.imageResult?.overlay_image_url || ''))
const imageClasses = computed(() => segmentStore.imageResult?.classes || [])

const videoOriginalUrl = computed(() => {
  return resolveAssetUrl(segmentStore.videoResult?.original_video_url || segmentStore.videoPreviewUrl)
})

const appendCacheBuster = (url: string, ts: number) => {
  if (!url) return ''
  const separator = url.includes('?') ? '&' : '?'
  return `${url}${separator}t=${ts}`
}

const videoOverlayUrl = computed(() => finalPlayableVideoUrl.value)
const videoPreviewImage = computed(() => {
  if (!segmentStore.videoPreviewBase64) {
    return ''
  }
  return `data:image/jpeg;base64,${segmentStore.videoPreviewBase64}`
})

const activeResultModelName = computed(() => {
  if (activeMode.value === 'video') {
    return segmentStore.videoResult?.model_name || segmentStore.videoSummary?.model_name || segmentStore.videoRuntimeModelName
  }
  return segmentStore.imageResult?.model_name
})

const activeInputSize = computed<[number, number] | undefined>(() => {
  if (activeMode.value === 'video') {
    return (
      segmentStore.videoResult?.input_size ||
      segmentStore.videoSummary?.input_size ||
      segmentStore.videoRuntimeInputSize ||
      undefined
    )
  }
  return segmentStore.imageResult?.input_size
})

const activeInferenceTime = computed<number | undefined>(() => {
  if (activeMode.value === 'video') {
    return segmentStore.videoResult?.inference_time || segmentStore.videoSummary?.inference_time
  }
  return segmentStore.imageResult?.inference_time
})

const activeRealtimeFps = computed<number | null>(() => {
  if (activeMode.value === 'video') {
    return segmentStore.videoRealtimeFps ?? segmentStore.videoSummary?.realtime_fps ?? segmentStore.videoResult?.realtime_fps ?? null
  }
  return null
})

const activeAvgFps = computed<number | null>(() => {
  if (activeMode.value === 'video') {
    return segmentStore.videoResult?.avg_fps ?? segmentStore.videoSummary?.avg_fps ?? null
  }
  return null
})

const activeModelName = computed(() => activeResultModelName.value || systemStore.modelInfo?.model_name)

const closeWs = () => {
  if (wsRef.value) {
    wsRef.value.close()
    wsRef.value = null
  }
}

const clearResultPolling = () => {
  if (resultPollTimer) {
    clearInterval(resultPollTimer)
    resultPollTimer = null
  }
  pollingBusy = false
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

const waitForVideoReady = async (videoUrl: string) => {
  if (!videoUrl) return false

  for (let i = 0; i < 12; i += 1) {
    const urlWithTs = `${videoUrl}${videoUrl.includes('?') ? '&' : '?'}ready=${Date.now()}`
    try {
      const res = await fetch(urlWithTs, {
        method: 'HEAD',
        cache: 'no-store',
      })
      if (res.ok) {
        return true
      }
    } catch {
      // keep retrying
    }
    await sleep(300)
  }

  return false
}

const canPlayVideoUrl = async (videoUrl: string, timeoutMs = 5000) => {
  if (!videoUrl) return false

  return new Promise<boolean>((resolve) => {
    const probe = document.createElement('video')
    let done = false

    const finish = (ok: boolean) => {
      if (done) return
      done = true
      clearTimeout(timer)
      probe.onloadedmetadata = null
      probe.onerror = null
      probe.src = ''
      resolve(ok)
    }

    const timer = window.setTimeout(() => finish(false), timeoutMs)

    probe.preload = 'metadata'
    probe.muted = true
    probe.playsInline = true
    probe.onloadedmetadata = () => finish(Boolean(probe.duration && Number.isFinite(probe.duration)))
    probe.onerror = () => finish(false)
    probe.src = videoUrl
    probe.load()
  })
}

const resolvePlayableResultVideo = async (overlayUrl: string, segmentedUrl: string) => {
  const candidates = [overlayUrl, segmentedUrl].filter(Boolean)

  for (const rawUrl of candidates) {
    const ready = await waitForVideoReady(rawUrl)
    if (!ready) {
      continue
    }
    const candidate = appendCacheBuster(rawUrl, Date.now())
    const playable = await canPlayVideoUrl(candidate)
    if (playable) {
      return candidate
    }
  }

  return ''
}

const applyFinalResultToPlayer = async (result: VideoSegmentResult | null) => {
  if (!result) return false

  const playableUrl = await resolvePlayableResultVideo(
    resolveAssetUrl(result.overlay_video_url),
    resolveAssetUrl(result.segmented_video_url),
  )

  finalPlayableVideoUrl.value = playableUrl
  return Boolean(playableUrl)
}

const pollFinalizeResult = (taskId: string) => {
  clearResultPolling()

  resultPollTimer = setInterval(async () => {
    if (pollingBusy) return
    pollingBusy = true

    try {
      const data = await fetchVideoFinalizeResult(taskId)
      segmentStore.applyVideoResultQueryResult(data)

      if (data.finalize_status === 'completed') {
        clearResultPolling()
        const ok = await applyFinalResultToPlayer(data.result)
        if (ok) {
          ElMessage.success('最终视频生成完成')
        } else {
          ElMessage.warning('最终视频已生成，但浏览器无法播放，请检查编码格式')
        }
      }

      if (data.finalize_status === 'failed') {
        clearResultPolling()
        segmentStore.applyVideoFinalizeFailed(data.message || '最终视频生成失败')
      }
    } catch (error) {
      clearResultPolling()
      segmentStore.applyVideoFinalizeFailed(error instanceof Error ? error.message : '查询最终视频结果失败')
    } finally {
      pollingBusy = false
    }
  }, 1500)
}

const startFinalizeFlow = async (taskId: string) => {
  if (!taskId || finalizingRequestedTaskId === taskId) {
    return
  }

  finalizingRequestedTaskId = taskId

  try {
    segmentStore.applyVideoFinalizeStarted('queued')
    const data = await triggerVideoFinalize(taskId)
    segmentStore.applyVideoFinalizeStarted(data.finalize_status)

    if (data.finalize_status === 'completed') {
      const resultData = await fetchVideoFinalizeResult(taskId)
      segmentStore.applyVideoResultQueryResult(resultData)
      const ok = await applyFinalResultToPlayer(resultData.result)
      if (ok) {
        ElMessage.success('最终视频生成完成')
      } else {
        ElMessage.warning('最终视频已生成，但浏览器无法播放，请检查编码格式')
      }
      return
    }

    if (data.finalize_status === 'failed') {
      segmentStore.applyVideoFinalizeFailed(data.message || '最终视频生成失败')
      return
    }

    pollFinalizeResult(taskId)
  } catch (error) {
    segmentStore.applyVideoFinalizeFailed(error instanceof Error ? error.message : '触发最终视频生成失败')
  }
}

const buildWsUrl = (wsPath: string) => {
  const withToken = (url: string) => {
    const token = getAccessToken()
    if (!token || /[?&]token=/.test(url)) {
      return url
    }
    const separator = url.includes('?') ? '&' : '?'
    return `${url}${separator}token=${encodeURIComponent(token)}`
  }

  if (wsPath.startsWith('ws://') || wsPath.startsWith('wss://')) {
    return withToken(wsPath)
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const normalizedPath = wsPath.startsWith('/') ? wsPath : `/${wsPath}`
  return withToken(`${protocol}//${window.location.host}${normalizedPath}`)
}

const handleVideoRealtimeEvent = async (eventData: VideoRealtimeEvent) => {
  if (eventData.type === 'task_snapshot') {
    segmentStore.applyVideoTaskSnapshot(eventData)

    if (eventData.status === 'failed' && eventData.message) {
      closeWs()
      clearResultPolling()
      return
    }

    if (eventData.finalize_status === 'completed' && eventData.result) {
      const ok = await applyFinalResultToPlayer(eventData.result)
      if (!ok) {
        ElMessage.warning('最终视频已生成，但浏览器无法播放，请检查编码格式')
      }
      closeWs()
      clearResultPolling()
      return
    }

    if (eventData.status === 'completed' && (eventData.finalize_status === 'idle' || eventData.finalize_status === 'queued')) {
      closeWs()
      await startFinalizeFlow(eventData.task_id)
      return
    }

    if (eventData.finalize_status === 'running') {
      pollFinalizeResult(eventData.task_id)
      return
    }

    return
  }

  if (eventData.type === 'task_started') {
    segmentStore.applyVideoTaskStarted(eventData)
    return
  }

  if (eventData.type === 'task_progress') {
    segmentStore.applyVideoTaskProgress(eventData)
    return
  }

  if (eventData.type === 'task_completed') {
    segmentStore.applyVideoTaskCompleted(eventData)
    ElMessage.success('实时预览阶段完成，正在生成最终视频')
    closeWs()
    await startFinalizeFlow(eventData.task_id)
    return
  }

  if (eventData.type === 'task_finalize_started') {
    segmentStore.applyVideoFinalizeStarted(eventData.finalize_status)
    return
  }

  if (eventData.type === 'task_finalize_completed') {
    segmentStore.applyVideoFinalizeCompleted(eventData.result)
    const ok = await applyFinalResultToPlayer(eventData.result)
    if (ok) {
      ElMessage.success('最终视频生成完成')
    } else {
      ElMessage.warning('最终视频已生成，但浏览器无法播放，请检查编码格式')
    }
    clearResultPolling()
    return
  }

  if (eventData.type === 'task_finalize_failed') {
    segmentStore.applyVideoFinalizeFailed(eventData.message)
    clearResultPolling()
    return
  }

  if (eventData.type === 'task_failed') {
    segmentStore.applyVideoTaskFailed(eventData.message)
    closeWs()
    clearResultPolling()
  }
}

const connectVideoWs = (wsPath: string) => {
  closeWs()
  const ws = new WebSocket(buildWsUrl(wsPath))
  wsRef.value = ws

  ws.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data) as VideoRealtimeEvent
      void handleVideoRealtimeEvent(payload)
    } catch {
      segmentStore.applyVideoTaskFailed('WebSocket 消息解析失败')
      closeWs()
      clearResultPolling()
    }
  }

  ws.onerror = () => {
    segmentStore.applyVideoTaskFailed('实时连接失败，请稍后重试')
  }

  ws.onclose = () => {
    wsRef.value = null
  }
}

const onModelChange = async (modelKey: ModelKey) => {
  await systemStore.setModelKey(modelKey)
  ElMessage.success('模型已切换')
}

const onImageFileSelect = (file: File) => {
  segmentStore.setImageFile(file)
}

const onVideoFileSelect = (file: File) => {
  clearResultPolling()
  finalizingRequestedTaskId = ''
  finalPlayableVideoUrl.value = ''
  segmentStore.setVideoFile(file)
}

const onImageResolutionChange = (resolution: string) => {
  segmentStore.setImageResolution(resolution)
}

const onVideoResolutionChange = (resolution: string) => {
  segmentStore.setVideoResolution(resolution)
}

const onImageRun = async () => {
  await segmentStore.runImageSegmentation(systemStore.selectedModelKey)
  if (segmentStore.imageResult) {
    ElMessage.success('图像分割完成')
  }
}

const onVideoRun = async () => {
  clearResultPolling()
  closeWs()
  finalizingRequestedTaskId = ''
  finalPlayableVideoUrl.value = ''

  const task = await segmentStore.createRealtimeVideoSegmentationTask(systemStore.selectedModelKey)
  if (!task) {
    return
  }

  connectVideoWs(task.ws_url)
  ElMessage.success('实时任务已创建，正在处理')
}

const onImageReset = () => {
  segmentStore.resetImage()
}

const onVideoReset = () => {
  clearResultPolling()
  closeWs()
  finalizingRequestedTaskId = ''
  finalPlayableVideoUrl.value = ''
  segmentStore.resetVideo()
}

watch(
  () => segmentStore.errorMessage,
  (message) => {
    if (message) {
      ElMessage.error(message)
    }
  },
)

onMounted(() => {
  if (!systemStore.modelInfo) {
    systemStore.loadModelInfo()
  }
  segmentStore.loadResolutionOptions()
})

onBeforeUnmount(() => {
  clearResultPolling()
  closeWs()
})
</script>

<style scoped>
:deep(.el-row + .el-row) {
  margin-top: 16px;
}

.mode-tabs {
  margin-top: 6px;
}
</style>
