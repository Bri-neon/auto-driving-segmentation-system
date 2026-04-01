<template>
  <PageContainer
    title="个人主页"
    description="管理你的个人资料、头像和登录密码。所有修改实时写入后端账号系统。"
  >
    <el-row :gutter="16" class="profile-row">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="profile-card">
          <template #header>个人资料</template>
          <el-form :model="profileForm" label-position="top">
            <el-form-item label="用户名">
              <el-input :model-value="authStore.user?.username || ''" disabled />
            </el-form-item>
            <el-form-item label="角色">
              <el-tag :type="authStore.isAdmin ? 'danger' : 'info'">{{ authStore.user?.role || 'user' }}</el-tag>
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" placeholder="请输入邮箱（可留空）" />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="profileForm.nickname" placeholder="请输入昵称（可留空）" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="savingProfile" @click="onSaveProfile">保存资料</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="security-card">
          <template #header>安全设置</template>
          <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-position="top">
            <el-form-item label="当前密码" prop="current_password">
              <el-input v-model="passwordForm.current_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="passwordForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirm_password">
              <el-input v-model="passwordForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="warning" :loading="changingPassword" @click="onChangePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </PageContainer>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import PageContainer from '../components/PageContainer.vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const savingProfile = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref<FormInstance>()

const profileForm = reactive({
  email: '',
  nickname: '',
})

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const passwordRules: FormRules = {
  current_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, max: 128, message: '新密码长度需在 8-128 位之间', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的新密码不一致'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
}

const syncProfileFromStore = () => {
  profileForm.email = authStore.user?.email || ''
  profileForm.nickname = authStore.user?.nickname || ''
}

const onSaveProfile = async () => {
  savingProfile.value = true
  try {
    await authStore.updateProfile({
      email: profileForm.email.trim() || null,
      nickname: profileForm.nickname.trim() || null,
    })
    ElMessage.success('个人资料已更新')
    syncProfileFromStore()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '更新个人资料失败')
  } finally {
    savingProfile.value = false
  }
}

const onChangePassword = async () => {
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  changingPassword.value = true
  try {
    await authStore.changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功，请使用新密码登录')
    passwordFormRef.value?.resetFields()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '修改密码失败')
  } finally {
    changingPassword.value = false
  }
}

onMounted(async () => {
  if (!authStore.user) {
    await authStore.refreshCurrentUser().catch(() => null)
  }
  syncProfileFromStore()
})
</script>

<style scoped>
.profile-row {
  margin-top: 8px;
}

.profile-card,
.security-card {
  height: 100%;
}
</style>
