<template>
  <el-container class="main-layout">
    <el-header class="main-header">
      <TopNav />
    </el-header>

    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import TopNav from '../components/TopNav.vue'
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  background: linear-gradient(180deg, #f5f7fb 0%, #edf1f7 100%);
}

.main-header {
  --el-header-padding: 0;
  height: 64px;
  border-bottom: 1px solid #d9e0ea;
  background: #ffffff;
  position: sticky;
  top: 0;
  z-index: 20;
}

.main-content {
  width: min(1400px, 100%);
  margin: 0 auto;
  padding: 24px;
}
</style>
