import { defineStore } from 'pinia'

import {
  createRealtimeVideoTask,
  fetchSegmentResolutions,
  segmentImage,
  segmentVideo,
  type ModelKey,
  type ResolutionOption,
  type SegmentResult,
  type VideoFinalizeQueryResult,
  type VideoFinalizeStatus,
  type VideoRealtimeStatus,
  type VideoRealtimeSummary,
  type VideoRealtimeTaskInit,
  type VideoSegmentResult,
} from '../api'

const fallbackResolutionOptions: ResolutionOption[] = [
  { key: '512x1024', input_size: [512, 1024], label: '512 x 1024（高精度）' },
  { key: '384x768', input_size: [384, 768], label: '384 x 768（均衡）' },
  { key: '320x640', input_size: [320, 640], label: '320 x 640（快速）' },
  { key: '256x512', input_size: [256, 512], label: '256 x 512（超快速）' },
]

interface SegmentState {
  imageFile: File | null
  videoFile: File | null
  imagePreviewUrl: string
  videoPreviewUrl: string
  imageResult: SegmentResult | null
  videoResult: VideoSegmentResult | null
  videoSummary: VideoRealtimeSummary | null
  videoTaskId: string
  videoWsUrl: string
  videoRealtimeStatus: VideoRealtimeStatus
  videoFinalizeStatus: VideoFinalizeStatus
  videoProgress: number
  videoFrameIndex: number
  videoTotalFrames: number
  videoRealtimeFps: number | null
  videoPreviewBase64: string
  videoRuntimeModelName: string
  videoRuntimeInputSize: [number, number] | null
  videoResultUpdatedAt: number
  imageResolutionOptions: ResolutionOption[]
  videoResolutionOptions: ResolutionOption[]
  defaultResolution: string
  selectedImageResolution: string
  selectedVideoResolution: string
  resolutionLoading: boolean
  imageLoading: boolean
  videoLoading: boolean
  errorMessage: string
}

export const useSegmentStore = defineStore('segment', {
  state: (): SegmentState => ({
    imageFile: null,
    videoFile: null,
    imagePreviewUrl: '',
    videoPreviewUrl: '',
    imageResult: null,
    videoResult: null,
    videoSummary: null,
    videoTaskId: '',
    videoWsUrl: '',
    videoRealtimeStatus: 'idle',
    videoFinalizeStatus: 'idle',
    videoProgress: 0,
    videoFrameIndex: 0,
    videoTotalFrames: 0,
    videoRealtimeFps: null,
    videoPreviewBase64: '',
    videoRuntimeModelName: '',
    videoRuntimeInputSize: null,
    videoResultUpdatedAt: 0,
    imageResolutionOptions: fallbackResolutionOptions,
    videoResolutionOptions: fallbackResolutionOptions,
    defaultResolution: '512x1024',
    selectedImageResolution: '512x1024',
    selectedVideoResolution: '512x1024',
    resolutionLoading: false,
    imageLoading: false,
    videoLoading: false,
    errorMessage: '',
  }),
  actions: {
    async loadResolutionOptions() {
      this.resolutionLoading = true
      try {
        const config = await fetchSegmentResolutions()
        const imageOptions = config.image_resolutions?.length ? config.image_resolutions : fallbackResolutionOptions
        const videoOptions = config.video_resolutions?.length ? config.video_resolutions : fallbackResolutionOptions
        const defaultResolution = config.default_resolution || imageOptions[0].key

        this.imageResolutionOptions = imageOptions
        this.videoResolutionOptions = videoOptions
        this.defaultResolution = defaultResolution

        if (!imageOptions.some((item) => item.key === this.selectedImageResolution)) {
          this.selectedImageResolution = imageOptions.some((item) => item.key === defaultResolution)
            ? defaultResolution
            : imageOptions[0].key
        }

        if (!videoOptions.some((item) => item.key === this.selectedVideoResolution)) {
          this.selectedVideoResolution = videoOptions.some((item) => item.key === defaultResolution)
            ? defaultResolution
            : videoOptions[0].key
        }
      } catch {
        this.imageResolutionOptions = fallbackResolutionOptions
        this.videoResolutionOptions = fallbackResolutionOptions
        this.defaultResolution = '512x1024'
      } finally {
        this.resolutionLoading = false
      }
    },

    setImageResolution(resolution: string) {
      this.selectedImageResolution = resolution
    },

    setVideoResolution(resolution: string) {
      this.selectedVideoResolution = resolution
    },

    setImageFile(file: File) {
      this.revokeImageUrls()
      this.imageFile = file
      this.imagePreviewUrl = URL.createObjectURL(file)
      this.imageResult = null
      this.errorMessage = ''
    },

    setVideoFile(file: File) {
      this.revokeVideoUrls()
      this.videoFile = file
      this.videoPreviewUrl = URL.createObjectURL(file)
      this.videoResult = null
      this.resetVideoRealtimeState()
      this.errorMessage = ''
    },

    revokeImageUrls() {
      if (this.imagePreviewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(this.imagePreviewUrl)
      }

      const urls = [
        this.imageResult?.original_image_url,
        this.imageResult?.segmented_image_url,
        this.imageResult?.overlay_image_url,
      ]

      urls.forEach((url) => {
        if (url?.startsWith('blob:')) {
          URL.revokeObjectURL(url)
        }
      })

      this.imagePreviewUrl = ''
    },

    revokeVideoUrls() {
      if (this.videoPreviewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(this.videoPreviewUrl)
      }

      const urls = [
        this.videoResult?.original_video_url,
        this.videoResult?.segmented_video_url,
        this.videoResult?.overlay_video_url,
      ]

      urls.forEach((url) => {
        if (url?.startsWith('blob:')) {
          URL.revokeObjectURL(url)
        }
      })

      this.videoPreviewUrl = ''
    },

    async runImageSegmentation(modelKey: ModelKey) {
      if (!this.imageFile) {
        this.errorMessage = '请先上传图片后再开始分割'
        return
      }

      this.imageLoading = true
      this.errorMessage = ''

      try {
        this.revokeImageResultUrlsOnly()
        this.imageResult = await segmentImage(this.imageFile, modelKey, this.selectedImageResolution)
      } catch (error) {
        this.errorMessage = error instanceof Error ? error.message : '图像分割失败，请稍后重试'
      } finally {
        this.imageLoading = false
      }
    },

    revokeImageResultUrlsOnly() {
      const urls = [
        this.imageResult?.original_image_url,
        this.imageResult?.segmented_image_url,
        this.imageResult?.overlay_image_url,
      ]

      urls.forEach((url) => {
        if (url?.startsWith('blob:')) {
          URL.revokeObjectURL(url)
        }
      })
    },

    async runVideoSegmentation(modelKey: ModelKey) {
      if (!this.videoFile) {
        this.errorMessage = '请先上传视频后再开始分割'
        return
      }

      this.videoLoading = true
      this.errorMessage = ''

      try {
        this.revokeVideoResultUrlsOnly()
        const result = await segmentVideo(this.videoFile, modelKey, this.selectedVideoResolution)
        this.videoResult = result
        this.videoRealtimeStatus = 'completed'
        this.videoFinalizeStatus = 'completed'
        this.videoRealtimeFps = result.realtime_fps
        this.videoSummary = {
          frame_count: 0,
          total_frames: 0,
          avg_fps: result.avg_fps,
          realtime_fps: result.realtime_fps,
          inference_time: result.inference_time,
          model_name: result.model_name,
          input_size: result.input_size,
        }
        this.videoRuntimeModelName = result.model_name
        this.videoRuntimeInputSize = result.input_size
        this.videoResultUpdatedAt = Date.now()
      } catch (error) {
        this.errorMessage = error instanceof Error ? error.message : '视频分割失败，请稍后重试'
      } finally {
        this.videoLoading = false
      }
    },

    async createRealtimeVideoSegmentationTask(modelKey: ModelKey): Promise<VideoRealtimeTaskInit | null> {
      if (!this.videoFile) {
        this.errorMessage = '请先上传视频后再开始分割'
        return null
      }

      this.videoLoading = true
      this.errorMessage = ''

      try {
        this.revokeVideoResultUrlsOnly()
        this.resetVideoRealtimeState()
        const task = await createRealtimeVideoTask(this.videoFile, modelKey, this.selectedVideoResolution)
        this.videoTaskId = task.task_id
        this.videoWsUrl = task.ws_url
        this.videoRealtimeStatus = task.status
        this.videoFinalizeStatus = task.finalize_status
        this.videoRuntimeModelName = task.model_name
        this.videoRuntimeInputSize = task.input_size
        return task
      } catch (error) {
        this.errorMessage = error instanceof Error ? error.message : '创建实时视频任务失败，请稍后重试'
        return null
      } finally {
        this.videoLoading = false
      }
    },

    applyVideoTaskSnapshot(payload: {
      status: VideoRealtimeStatus
      finalize_status: VideoFinalizeStatus
      summary: VideoRealtimeSummary | null
      result: VideoSegmentResult | null
      message: string | null
    }) {
      this.videoRealtimeStatus = payload.status
      this.videoFinalizeStatus = payload.finalize_status

      if (payload.summary) {
        this.videoSummary = payload.summary
        this.videoRealtimeFps = payload.summary.realtime_fps
        this.videoRuntimeModelName = payload.summary.model_name
        this.videoRuntimeInputSize = payload.summary.input_size
      }

      if (payload.result) {
        this.videoResult = payload.result
        this.videoResultUpdatedAt = Date.now()
      }

      if (payload.message) {
        this.errorMessage = payload.message
      }
    },

    applyVideoTaskStarted(payload: {
      model_name: string
      input_size: [number, number]
      finalize_status: VideoFinalizeStatus
    }) {
      this.videoRealtimeStatus = 'running'
      this.videoFinalizeStatus = payload.finalize_status
      this.videoRuntimeModelName = payload.model_name
      this.videoRuntimeInputSize = payload.input_size
    },

    applyVideoTaskProgress(payload: {
      frame_index: number
      total_frames: number
      progress: number
      realtime_fps: number
      inference_time: number
      preview_jpeg_base64: string
      finalize_status?: VideoFinalizeStatus
    }) {
      this.videoRealtimeStatus = 'running'
      if (payload.finalize_status) {
        this.videoFinalizeStatus = payload.finalize_status
      }
      this.videoFrameIndex = payload.frame_index
      this.videoTotalFrames = payload.total_frames
      this.videoProgress = payload.progress
      this.videoRealtimeFps = payload.realtime_fps
      this.videoPreviewBase64 = payload.preview_jpeg_base64

      if (this.videoSummary) {
        this.videoSummary.inference_time = payload.inference_time
        this.videoSummary.realtime_fps = payload.realtime_fps
      }
    },

    applyVideoTaskCompleted(payload: { finalize_status: VideoFinalizeStatus; summary: VideoRealtimeSummary }) {
      this.videoRealtimeStatus = 'completed'
      this.videoFinalizeStatus = payload.finalize_status
      this.videoSummary = payload.summary
      this.videoProgress = 100
      this.videoFrameIndex = payload.summary.frame_count
      this.videoTotalFrames = payload.summary.total_frames
      this.videoRealtimeFps = payload.summary.realtime_fps
      this.videoRuntimeModelName = payload.summary.model_name
      this.videoRuntimeInputSize = payload.summary.input_size
      this.videoPreviewBase64 = ''
    },

    applyVideoFinalizeStarted(status: VideoFinalizeStatus = 'running') {
      this.videoFinalizeStatus = status
    },

    applyVideoFinalizeCompleted(result: VideoSegmentResult | null) {
      this.videoFinalizeStatus = 'completed'
      if (result) {
        this.videoResult = result
        this.videoRealtimeFps = result.realtime_fps
        this.videoRuntimeModelName = result.model_name
        this.videoRuntimeInputSize = result.input_size
        this.videoResultUpdatedAt = Date.now()
      }
    },

    applyVideoResultQueryResult(payload: VideoFinalizeQueryResult) {
      this.videoRealtimeStatus = payload.realtime_status
      this.videoFinalizeStatus = payload.finalize_status

      if (payload.summary) {
        this.videoSummary = payload.summary
        this.videoRealtimeFps = payload.summary.realtime_fps
        this.videoRuntimeModelName = payload.summary.model_name
        this.videoRuntimeInputSize = payload.summary.input_size
      }

      if (payload.result) {
        this.videoResult = payload.result
        this.videoResultUpdatedAt = Date.now()
      }

      if (payload.message && payload.finalize_status === 'failed') {
        this.errorMessage = payload.message
      }
    },

    applyVideoTaskFailed(message: string) {
      this.videoRealtimeStatus = 'failed'
      this.errorMessage = message
    },

    applyVideoFinalizeFailed(message: string) {
      this.videoFinalizeStatus = 'failed'
      this.errorMessage = message
    },

    resetVideoRealtimeState() {
      this.videoTaskId = ''
      this.videoWsUrl = ''
      this.videoRealtimeStatus = 'idle'
      this.videoFinalizeStatus = 'idle'
      this.videoSummary = null
      this.videoProgress = 0
      this.videoFrameIndex = 0
      this.videoTotalFrames = 0
      this.videoRealtimeFps = null
      this.videoPreviewBase64 = ''
      this.videoRuntimeModelName = ''
      this.videoRuntimeInputSize = null
      this.videoResultUpdatedAt = 0
      this.videoResult = null
    },

    revokeVideoResultUrlsOnly() {
      const urls = [
        this.videoResult?.original_video_url,
        this.videoResult?.segmented_video_url,
        this.videoResult?.overlay_video_url,
      ]

      urls.forEach((url) => {
        if (url?.startsWith('blob:')) {
          URL.revokeObjectURL(url)
        }
      })
    },

    resetImage() {
      this.revokeImageUrls()
      this.imageFile = null
      this.imageResult = null
      this.imageLoading = false
      this.errorMessage = ''
    },

    resetVideo() {
      this.revokeVideoUrls()
      this.videoFile = null
      this.videoLoading = false
      this.resetVideoRealtimeState()
      this.errorMessage = ''
    },
  },
})
