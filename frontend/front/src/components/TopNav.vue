<template>
  <nav class="top-nav">
    <div class="brand" @click="goHome">
      <div class="brand-dot" />
      <div class="brand-text">
        <strong>{{ systemStore.title }}</strong>
        <span>{{ systemStore.subtitle }}</span>
      </div>
    </div>

    <el-menu class="menu" mode="horizontal" :default-active="activePath" @select="onSelect">
      <el-menu-item index="/">系统介绍</el-menu-item>
      <el-menu-item index="/segment">图像分割</el-menu-item>
      <el-menu-item index="/history">推理历史</el-menu-item>
      <el-menu-item index="/profile">个人主页</el-menu-item>
      <el-menu-item v-if="authStore.isAdmin" index="/admin">管理后台</el-menu-item>
      <el-menu-item index="/about">关于系统</el-menu-item>
    </el-menu>

    <div class="auth-actions">
      <template v-if="authStore.isAuthenticated">
        <el-upload
          class="avatar-uploader"
          :show-file-list="false"
          :auto-upload="false"
          :accept="'image/png,image/jpg,image/jpeg'"
          :on-change="onAvatarSelect"
        >
          <el-tooltip content="点击上传头像（JPG / PNG）" placement="bottom">
            <el-avatar :size="38" :src="avatarUrl" class="user-avatar">
              {{ authStore.displayName.slice(0, 1).toUpperCase() || 'U' }}
            </el-avatar>
          </el-tooltip>
        </el-upload>

        <span class="user-name">
          {{ authStore.displayName || '用户' }}
          <em v-if="authStore.isAdmin">管理员</em>
        </span>

        <el-button text type="danger" @click="onLogout">退出登录</el-button>
      </template>
      <template v-else>
        <el-button type="primary" @click="goLogin">登录 / 注册</el-button>
      </template>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { type UploadFile, ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { useSystemStore } from '../stores/system'
import { resolveAssetUrl } from '../utils/format'

const route = useRoute()
const router = useRouter()
const systemStore = useSystemStore()
const authStore = useAuthStore()

const activePath = computed(() => route.path)
const avatarUrl = computed(() => resolveAssetUrl(authStore.user?.avatar_url || ''))

const onSelect = (path: string) => {
  if (path !== route.path) {
    void router.push(path)
  }
}

const goHome = () => {
  if (route.path !== '/') {
    void router.push('/')
  }
}

const goLogin = () => {
  if (route.path !== '/login') {
    void router.push({ name: 'login', query: { redirect: route.fullPath || '/segment' } })
  }
}

const onLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  if (route.path !== '/login') {
    void router.push({ name: 'login' })
  }
}

const onAvatarSelect = async (file: UploadFile) => {
  if (!file.raw) {
    return
  }
  try {
    await authStore.updateAvatar(file.raw)
    ElMessage.success('头像更新成功')
    await authStore.refreshCurrentUser()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '头像上传失败')
  }
}

onMounted(() => {
  if (authStore.isAuthenticated && !authStore.user) {
    authStore.refreshCurrentUser().catch(() => {
      authStore.logout()
    })
  }
})
</script>

<style scoped>
.top-nav {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 18px;
  height: 100%;
  padding: 0 24px;
}

.brand {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.brand-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4da3ff, #ffd166);
  box-shadow: 0 0 14px rgba(77, 163, 255, 0.45);
}

.brand-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.brand-text strong {
  font-size: 18px;
  line-height: 1.1;
  color: #0e2238;
}

.brand-text span {
  margin-top: 4px;
  font-size: 12px;
  color: #58708c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu {
  min-width: 0;
  border-bottom: none;
  background: transparent;
}

.menu :deep(.el-menu--horizontal) {
  background: transparent;
  border-bottom: none;
}

.menu :deep(.el-menu-item) {
  border-bottom: none !important;
  color: #2a4461;
}

.menu :deep(.el-menu-item.is-active) {
  color: #1677d2;
  font-weight: 600;
  background: rgba(77, 163, 255, 0.1);
  border-radius: 10px;
}

.auth-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar-uploader {
  display: inline-flex;
}

.user-avatar {
  box-shadow: 0 8px 18px rgba(77, 163, 255, 0.2);
}

.user-name {
  max-width: 180px;
  font-size: 13px;
  color: #2d4867;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-name em {
  margin-left: 6px;
  font-style: normal;
  color: #0f6bb5;
  font-weight: 600;
}

@media (max-width: 1240px) {
  .top-nav {
    grid-template-columns: 1fr;
    height: auto;
    padding-top: 8px;
    padding-bottom: 8px;
  }

  .auth-actions {
    justify-content: flex-end;
  }
}
</style>
