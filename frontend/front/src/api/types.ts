export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export type ModelKey = 'deeplabv3plus_resnet50' | 'bisenetv2'

export interface ModelOption {
  label: string
  value: ModelKey
}

export interface SegmentClassItem {
  name: string
  color: string
  ratio: number
}

export interface ResolutionOption {
  key: string
  input_size: [number, number]
  label: string
}

export interface SegmentResolutionConfig {
  image_resolutions: ResolutionOption[]
  video_resolutions: ResolutionOption[]
  default_resolution: string
}

export interface SegmentResult {
  original_image_url: string
  segmented_image_url: string
  overlay_image_url: string
  inference_time: number
  model_name: string
  input_size: [number, number]
  classes: SegmentClassItem[]
}

export interface VideoSegmentResult {
  original_video_url: string
  segmented_video_url: string
  overlay_video_url: string
  avg_fps: number
  realtime_fps: number
  inference_time: number
  model_name: string
  input_size: [number, number]
}

export type VideoRealtimeStatus = 'idle' | 'queued' | 'running' | 'completed' | 'failed'
export type VideoFinalizeStatus = 'idle' | 'queued' | 'running' | 'completed' | 'failed'

export interface VideoRealtimeSummary {
  frame_count: number
  total_frames: number
  avg_fps: number
  realtime_fps: number
  inference_time: number
  model_name: string
  input_size: [number, number]
}

export interface VideoRealtimeTaskInit {
  task_id: string
  ws_url: string
  status: VideoRealtimeStatus
  finalize_status: VideoFinalizeStatus
  original_video_url: string
  segmented_video_url: string
  overlay_video_url: string
  model_name: string
  input_size: [number, number]
}

export interface VideoFinalizeTriggerResult {
  task_id: string
  realtime_status: VideoRealtimeStatus
  finalize_status: VideoFinalizeStatus
  message: string | null
}

export interface VideoFinalizeQueryResult {
  task_id: string
  realtime_status: VideoRealtimeStatus
  finalize_status: VideoFinalizeStatus
  summary: VideoRealtimeSummary | null
  result: VideoSegmentResult | null
  message: string | null
}

export type VideoRealtimeEvent =
  | VideoTaskSnapshotEvent
  | VideoTaskStartedEvent
  | VideoTaskProgressEvent
  | VideoTaskCompletedEvent
  | VideoTaskFinalizeStartedEvent
  | VideoTaskFinalizeCompletedEvent
  | VideoTaskFinalizeFailedEvent
  | VideoTaskFailedEvent

export interface VideoTaskSnapshotEvent {
  type: 'task_snapshot'
  task_id: string
  status: VideoRealtimeStatus
  finalize_status: VideoFinalizeStatus
  summary: VideoRealtimeSummary | null
  result: VideoSegmentResult | null
  message: string | null
}

export interface VideoTaskStartedEvent {
  type: 'task_started'
  task_id: string
  status: 'running'
  finalize_status: VideoFinalizeStatus
  model_name: string
  input_size: [number, number]
  original_video_url: string
}

export interface VideoTaskProgressEvent {
  type: 'task_progress'
  task_id: string
  status: 'running'
  finalize_status?: VideoFinalizeStatus
  frame_index: number
  total_frames: number
  progress: number
  realtime_fps: number
  inference_time: number
  preview_jpeg_base64: string
}

export interface VideoTaskCompletedEvent {
  type: 'task_completed'
  task_id: string
  status: 'completed'
  finalize_status: VideoFinalizeStatus
  summary: VideoRealtimeSummary
}

export interface VideoTaskFinalizeStartedEvent {
  type: 'task_finalize_started'
  task_id: string
  status: VideoRealtimeStatus
  finalize_status: 'running' | 'queued'
}

export interface VideoTaskFinalizeCompletedEvent {
  type: 'task_finalize_completed'
  task_id: string
  status: VideoRealtimeStatus
  finalize_status: 'completed'
  result: VideoSegmentResult | null
}

export interface VideoTaskFinalizeFailedEvent {
  type: 'task_finalize_failed'
  task_id: string
  status: VideoRealtimeStatus
  finalize_status: 'failed'
  message: string
}

export interface VideoTaskFailedEvent {
  type: 'task_failed'
  task_id: string
  status: 'failed'
  message: string
}

export interface ModelInfo {
  model_key: ModelKey
  model_name: string
  framework: string
  backend: string
  input_size: [number, number]
  dataset: string
}
