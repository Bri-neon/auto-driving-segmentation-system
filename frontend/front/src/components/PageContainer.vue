<template>
  <section class="page-container">
    <header class="page-header" v-if="title || description">
      <h1 v-if="title">{{ title }}</h1>
      <p v-if="description">{{ description }}</p>
    </header>
    <slot />
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
}>()
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  color: #132238;
}

.page-header p {
  margin: 8px 0 0;
  color: #5f7085;
  max-width: 920px;
  line-height: 1.6;
}
</style>
