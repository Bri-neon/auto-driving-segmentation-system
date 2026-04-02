<template>
  <el-card shadow="never" class="result-card">
    <template #header>
      <div class="card-header">{{ title }}</div>
    </template>

    <div class="image-wrap" v-if="imageUrl">
      <img :src="imageUrl" :alt="title" />
    </div>
    <el-empty v-else :description="emptyText" :image-size="82" />
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
}

.card-header {
  font-weight: 600;
  color: var(--card-header-color);
}

.image-wrap {
  width: 100%;
  aspect-ratio: 16 / 9;
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
</style>
