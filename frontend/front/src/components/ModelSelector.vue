<template>
  <el-card shadow="never" class="selector-card">
    <template #header>
      <div class="card-header">模型选择</div>
    </template>

    <el-form label-position="top">
      <el-form-item label="分割模型">
        <el-select :model-value="modelKey" placeholder="请选择模型" @change="onChange" style="width: 100%">
          <el-option
            v-for="item in options"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import type { ModelKey, ModelOption } from '../api'

const emit = defineEmits<{
  (event: 'change', value: ModelKey): void
}>()

const props = defineProps<{
  modelKey: ModelKey
  options: ModelOption[]
}>()

const onChange = (value: ModelKey) => {
  if (value !== props.modelKey) {
    emit('change', value)
  }
}
</script>

<style scoped>
.selector-card {
  height: 100%;
}

.card-header {
  font-weight: 600;
  color: var(--card-header-color);
}
</style>
