<template>
  <nav class="top-nav">
    <div class="brand">
      <strong>{{ systemStore.title }}</strong>
      <span>{{ systemStore.subtitle }}</span>
    </div>

    <el-menu
      class="menu"
      mode="horizontal"
      :default-active="activePath"
      @select="onSelect"
    >
      <el-menu-item index="/">系统介绍</el-menu-item>
      <el-menu-item index="/segment">图像分割</el-menu-item>
      <el-menu-item index="/about">关于系统</el-menu-item>
    </el-menu>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useSystemStore } from '../stores/system'

const route = useRoute()
const router = useRouter()
const systemStore = useSystemStore()

const activePath = computed(() => route.path)

const onSelect = (path: string) => {
  if (path !== route.path) {
    router.push(path)
  }
}
</script>

<style scoped>
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 24px;
  gap: 24px;
}

.brand {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.brand strong {
  font-size: 18px;
  color: #152033;
  line-height: 1.1;
}

.brand span {
  font-size: 12px;
  color: #65758b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu {
  border-bottom: none;
}

@media (max-width: 900px) {
  .top-nav {
    flex-direction: column;
    align-items: stretch;
    justify-content: center;
    padding-top: 8px;
    padding-bottom: 8px;
    height: auto;
  }

  .brand span {
    white-space: normal;
  }
}
</style>
