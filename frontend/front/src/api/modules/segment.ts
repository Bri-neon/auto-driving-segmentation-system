import request from '../request'

import type {
  ApiResponse,
  ModelKey,
  SegmentResolutionConfig,
  SegmentResult,
  VideoFinalizeQueryResult,
  VideoFinalizeTriggerResult,
  VideoRealtimeTaskInit,
  VideoSegmentResult,
} from '../types'

export async function fetchSegmentResolutions(): Promise<SegmentResolutionConfig> {
  const { data } = await request.get<ApiResponse<SegmentResolutionConfig>>('/api/segment/resolutions')
  return data.data
}

export async function segmentImage(file: File, modelKey: ModelKey, resolution?: string): Promise<SegmentResult> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('model_key', modelKey)
  if (resolution) {
    formData.append('resolution', resolution)
  }

  const { data } = await request.post<ApiResponse<SegmentResult>>('/api/segment', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return data.data
}

export async function segmentVideo(file: File, modelKey: ModelKey, resolution?: string): Promise<VideoSegmentResult> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('model_key', modelKey)
  if (resolution) {
    formData.append('resolution', resolution)
  }

  const { data } = await request.post<ApiResponse<VideoSegmentResult>>('/api/segment/video', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return data.data
}

export async function createRealtimeVideoTask(
  file: File,
  modelKey: ModelKey,
  resolution?: string,
): Promise<VideoRealtimeTaskInit> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('model_key', modelKey)
  if (resolution) {
    formData.append('resolution', resolution)
  }

  const { data } = await request.post<ApiResponse<VideoRealtimeTaskInit>>('/api/segment/video/realtime', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return data.data
}

export async function triggerVideoFinalize(taskId: string): Promise<VideoFinalizeTriggerResult> {
  const { data } = await request.post<ApiResponse<VideoFinalizeTriggerResult>>(`/api/segment/video/finalize/${taskId}`)
  return data.data
}

export async function fetchVideoFinalizeResult(taskId: string): Promise<VideoFinalizeQueryResult> {
  const { data } = await request.get<ApiResponse<VideoFinalizeQueryResult>>(`/api/segment/video/result/${taskId}`)
  return data.data
}
