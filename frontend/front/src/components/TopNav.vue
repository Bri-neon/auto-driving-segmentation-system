<template>
  <nav class="top-nav">
    <div class="brand">
      <strong>{{ systemStore.title }}</strong>
      <span>{{ systemStore.subtitle }}</span>
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
          <el-tooltip content="点击上传头像（JPG/PNG）" placement="bottom">
            <el-avatar :size="36" :src="avatarUrl">
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 24px;
  gap: 20px;
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
  flex: 1;
  min-width: 0;
  border-bottom: none;
}

.auth-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.avatar-uploader {
  display: inline-flex;
}

.user-name {
  font-size: 13px;
  color: #314860;
  max-width: 160px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-name em {
  margin-left: 6px;
  color: #0f6bb5;
  font-style: normal;
}

@media (max-width: 1080px) {
  .top-nav {
    flex-direction: column;
    align-items: stretch;
    justify-content: center;
    padding-top: 8px;
    padding-bottom: 8px;
    height: auto;
  }

  .menu {
    width: 100%;
  }

  .auth-actions {
    justify-content: flex-end;
  }

  .brand span {
    white-space: normal;
  }
}
</style>
