<template>
  <el-card shadow="never" class="panel-card">
    <template #header>
      <div class="card-header">{{ title }}</div>
    </template>

    <el-form label-position="top" class="resolution-form">
      <el-form-item label="输入分辨率">
        <el-select
          :model-value="selectedResolution"
          placeholder="请选择分辨率"
          :loading="resolutionLoading"
          style="width: 100%"
          @change="onResolutionChange"
        >
          <el-option
            v-for="item in resolutionOptions"
            :key="item.key"
            :label="item.label"
            :value="item.key"
          />
        </el-select>
      </el-form-item>
    </el-form>

    <el-upload
      drag
      :show-file-list="false"
      :auto-upload="false"
      :accept="accept"
      :on-change="handleFileChange"
    >
      <div class="upload-inner">
        <p class="upload-title">{{ dragText }}</p>
        <p class="upload-tip">{{ tipText }}</p>
      </div>
    </el-upload>

    <div class="actions">
      <el-button type="primary" :disabled="!hasFile" :loading="loading" @click="$emit('run')">
        开始分割
      </el-button>
      <el-button @click="$emit('reset')">重置</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { UploadFile } from 'element-plus'
import type { ResolutionOption } from '../api'

const emit = defineEmits<{
  (event: 'select', file: File): void
  (event: 'resolution-change', resolution: string): void
  (event: 'run'): void
  (event: 'reset'): void
}>()

const props = defineProps<{
  loading: boolean
  hasFile: boolean
  mode?: 'image' | 'video'
  selectedResolution: string
  resolutionOptions: ResolutionOption[]
  resolutionLoading?: boolean
}>()

const isVideo = computed(() => props.mode === 'video')
const title = computed(() => (isVideo.value ? '视频上传' : '图片上传'))
const accept = computed(() => (isVideo.value ? 'video/mp4,video/avi,video/mov' : 'image/png,image/jpeg,image/jpg'))
const dragText = computed(() => (isVideo.value ? '拖拽视频到此处，或点击上传' : '拖拽图片到此处，或点击上传'))
const tipText = computed(() =>
  isVideo.value
    ? '支持 MP4 / AVI / MOV，建议使用道路场景测试视频'
    : '支持 JPG / PNG，建议自动驾驶道路场景图像',
)

const handleFileChange = (file: UploadFile) => {
  if (file.raw) {
    emit('select', file.raw)
  }
}

const onResolutionChange = (resolution: string) => {
  if (resolution !== props.selectedResolution) {
    emit('resolution-change', resolution)
  }
}
</script>

<style scoped>
.panel-card {
  height: 100%;
}

.card-header {
  font-weight: 600;
  color: #1d2c43;
}

.resolution-form {
  margin-bottom: 8px;
}

.upload-inner {
  padding: 12px;
}

.upload-title {
  margin: 0;
  font-size: 15px;
  color: #21344d;
}

.upload-tip {
  margin: 8px 0 0;
  font-size: 13px;
  color: #738399;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}
</style>
