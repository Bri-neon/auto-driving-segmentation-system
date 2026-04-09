<template>
  <el-card shadow="never" class="result-card">
    <template #header>
      <div class="card-header">{{ title }}</div>
    </template>

    <div class="media-slot">
      <div class="image-wrap" v-if="imageUrl">
        <img :src="imageUrl" :alt="title" />
      </div>
      <el-empty v-else :description="emptyText" :image-size="82" class="media-empty" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  imageUrl?: string
  emptyText?: string
}>()
</script>

<style scoped>
.result-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  font-weight: 600;
  color: var(--card-header-color);
}

.result-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 16px 14px;
}

.media-slot {
  width: 100%;
  height: 260px;
  min-height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 10px 0;
}

.image-wrap {
  width: 100%;
  height: 100%;
  background: var(--input-surface);
  border-radius: 8px;
  border: 1px solid var(--table-border-color);
  overflow: hidden;
}

.image-wrap img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.media-empty {
  width: 100%;
  height: 100%;
}

.media-empty :deep(.el-empty) {
  height: 100%;
}
</style>
