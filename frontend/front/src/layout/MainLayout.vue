<template>
  <el-container class="main-layout">
    <div class="ambient ambient-a" />
    <div class="ambient ambient-b" />

    <el-header class="main-header">
      <TopNav />
    </el-header>

    <el-main :class="['main-content', { 'main-content-home': isHome }]">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import TopNav from '../components/TopNav.vue'

const route = useRoute()
const isHome = computed(() => route.path === '/')
</script>

<style scoped>
.main-layout {
  position: relative;
  min-height: 100vh;
  background: transparent;
}

.ambient {
  position: fixed;
  z-index: 0;
  pointer-events: none;
  filter: blur(48px);
  opacity: 0.5;
}

.ambient-a {
  width: 340px;
  height: 340px;
  right: -120px;
  top: -80px;
  background: radial-gradient(circle, rgba(77, 163, 255, 0.42), transparent 65%);
}

.ambient-b {
  width: 320px;
  height: 320px;
  left: -130px;
  bottom: 8vh;
  background: radial-gradient(circle, rgba(255, 209, 102, 0.28), transparent 70%);
}

.main-header {
  --el-header-padding: 0;
  height: 74px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.42);
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  position: sticky;
  top: 0;
  z-index: 30;
}

.main-content {
  position: relative;
  z-index: 1;
  width: min(1440px, 100%);
  margin: 0 auto;
  padding: 26px;
}

.main-content-home {
  width: 100%;
  margin: 0;
  padding: 0;
}
</style>
