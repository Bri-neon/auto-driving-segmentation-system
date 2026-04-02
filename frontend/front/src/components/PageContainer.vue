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

.page-header {
  padding: 20px 22px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.48);
  border: 1px solid rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 8px 26px rgba(20, 60, 120, 0.09);
}

.page-header h1 {
  margin: 0;
  font-size: 30px;
  letter-spacing: -0.02em;
  color: #0e2238;
}

.page-header p {
  margin: 8px 0 0;
  color: #4f6783;
  max-width: 920px;
  line-height: 1.7;
}
</style>
