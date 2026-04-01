<template>
  <el-card shadow="never" class="info-card">
    <template #header>
      <div class="card-header">推理信息</div>
    </template>

    <el-descriptions :column="1" border>
      <el-descriptions-item label="模型名称">{{ modelName }}</el-descriptions-item>
      <el-descriptions-item label="后端框架">{{ backend }}</el-descriptions-item>
      <el-descriptions-item label="输入尺寸">{{ inputSizeText }}</el-descriptions-item>
      <el-descriptions-item label="单帧耗时">{{ inferenceTimeText }}</el-descriptions-item>
      <el-descriptions-item label="实时 FPS">{{ realtimeFpsText }}</el-descriptions-item>
      <el-descriptions-item label="平均 FPS">{{ avgFpsText }}</el-descriptions-item>
      <el-descriptions-item label="数据集">{{ dataset }}</el-descriptions-item>
    </el-descriptions>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { ModelInfo } from '../api'
import { formatMs } from '../utils/format'

const props = defineProps<{
  modelInfo: ModelInfo | null
  modelName?: string
  inputSize?: [number, number]
  inferenceTime?: number
  realtimeFps?: number | null
  avgFps?: number | null
}>()

const modelName = computed(() => props.modelName || props.modelInfo?.model_name || '待获取')
const backend = computed(() => props.modelInfo?.backend || 'FastAPI (planned)')
const inputSizeText = computed(() => {
  const input = props.inputSize || props.modelInfo?.input_size
  return input ? `${input[0]} x ${input[1]}` : '待获取'
})

const inferenceTimeText = computed(() => {
  if (props.inferenceTime === undefined) {
    return '等待推理'
  }
  return formatMs(props.inferenceTime)
})

const realtimeFpsText = computed(() => {
  if (props.realtimeFps === null || props.realtimeFps === undefined) {
    return '等待推理'
  }
  return `${props.realtimeFps.toFixed(1)} FPS`
})

const avgFpsText = computed(() => {
  if (props.avgFps === null || props.avgFps === undefined) {
    return '等待推理'
  }
  return `${props.avgFps.toFixed(1)} FPS`
})

const dataset = computed(() => props.modelInfo?.dataset || 'Cityscapes')
</script>

<style scoped>
.info-card {
  height: 100%;
}

.card-header {
  font-weight: 600;
  color: #1d2c43;
}
</style>
