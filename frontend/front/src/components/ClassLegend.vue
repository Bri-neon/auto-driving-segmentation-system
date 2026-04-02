<template>
  <el-card shadow="never" class="legend-card">
    <template #header>
      <div class="card-header">类别信息</div>
    </template>

    <el-table :data="classes" stripe size="small" empty-text="暂无类别信息">
      <el-table-column label="颜色" width="88">
        <template #default="scope">
          <span class="color-dot" :style="{ backgroundColor: scope.row.color }" />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="类别" min-width="120" />
      <el-table-column prop="ratio" label="占比(%)" min-width="120">
        <template #default="scope">
          {{ Number(scope.row.ratio).toFixed(2) }}
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import type { SegmentClassItem } from '../api'

defineProps<{
  classes: SegmentClassItem[]
}>()
</script>

<style scoped>
.legend-card {
  height: 100%;
}

.card-header {
  font-weight: 600;
  color: var(--card-header-color);
}

.color-dot {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  display: inline-block;
  border: 1px solid var(--table-border-color);
}
</style>
