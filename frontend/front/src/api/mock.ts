import heroImage from '../assets/hero.png'

import type {
  ModelInfo,
  ModelKey,
  ModelOption,
  SegmentResult,
  VideoSegmentResult,
} from './types'

const mockClasses = [
  { name: 'road', color: '#804080', ratio: 35.2 },
  { name: 'sidewalk', color: '#f423e8', ratio: 12.6 },
  { name: 'building', color: '#464646', ratio: 18.9 },
  { name: 'car', color: '#ff0000', ratio: 8.7 },
  { name: 'person', color: '#dc143c', ratio: 2.3 },
]

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export const modelOptions: ModelOption[] = [
  { label: 'DeepLabV3+ ResNet50', value: 'deeplabv3plus_resnet50' },
  { label: 'BiSeNetV2', value: 'bisenetv2' },
]

const modelInfoMap: Record<ModelKey, ModelInfo> = {
  deeplabv3plus_resnet50: {
    model_key: 'deeplabv3plus_resnet50',
    model_name: 'DeepLabV3+ ResNet50 FP16',
    framework: 'ONNX Runtime',
    backend: 'FastAPI (planned)',
    input_size: [512, 512],
    dataset: 'Cityscapes',
  },
  bisenetv2: {
    model_key: 'bisenetv2',
    model_name: 'BiSeNetV2 FP16',
    framework: 'ONNX Runtime',
    backend: 'FastAPI (planned)',
    input_size: [512, 1024],
    dataset: 'Cityscapes',
  },
}

export function getMockModelInfo(modelKey: ModelKey): ModelInfo {
  return modelInfoMap[modelKey]
}

export async function mockSegmentResult(
  originalImageUrl?: string,
  modelKey: ModelKey = 'bisenetv2',
): Promise<SegmentResult> {
  await wait(900)

  const imageUrl = originalImageUrl || heroImage
  const modelInfo = getMockModelInfo(modelKey)

  return {
    original_image_url: imageUrl,
    segmented_image_url: imageUrl,
    overlay_image_url: imageUrl,
    inference_time: modelKey === 'bisenetv2' ? 0.032 : 0.048,
    model_name: modelInfo.model_name,
    input_size: modelInfo.input_size,
    classes: mockClasses,
  }
}

export async function mockVideoSegmentResult(
  originalVideoUrl?: string,
  modelKey: ModelKey = 'bisenetv2',
): Promise<VideoSegmentResult> {
  await wait(1300)

  const videoUrl = originalVideoUrl || ''
  const modelInfo = getMockModelInfo(modelKey)
  const fpsBase = modelKey === 'bisenetv2' ? 68 : 45

  return {
    original_video_url: videoUrl,
    segmented_video_url: videoUrl,
    overlay_video_url: videoUrl,
    avg_fps: fpsBase,
    realtime_fps: fpsBase + 1.4,
    inference_time: modelKey === 'bisenetv2' ? 0.014 : 0.022,
    model_name: modelInfo.model_name,
    input_size: modelInfo.input_size,
  }
}

export const mockModelInfo = getMockModelInfo('bisenetv2')
