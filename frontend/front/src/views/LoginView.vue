<template>
  <PageContainer
    title="账号登录"
    description="登录后可访问受保护的分割接口、个人主页和推理历史；管理员可进入管理后台。"
  >
    <el-row :gutter="16" class="auth-row">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="auth-card">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="登录" name="login">
              <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" label-position="top">
                <el-form-item label="用户名" prop="username">
                  <el-input v-model="loginForm.username" placeholder="请输入用户名" />
                </el-form-item>
                <el-form-item label="密码" prop="password">
                  <el-input v-model="loginForm.password" type="password" show-password placeholder="请输入密码" />
                </el-form-item>
                <el-button type="primary" :loading="authStore.loading" @click="onLogin">
                  登录并进入系统
                </el-button>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="注册" name="register">
              <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" label-position="top">
                <el-form-item label="用户名" prop="username">
                  <el-input v-model="registerForm.username" placeholder="3-32 位，字母数字下划线" />
                </el-form-item>
                <el-form-item label="密码" prop="password">
                  <el-input v-model="registerForm.password" type="password" show-password placeholder="至少 8 位" />
                </el-form-item>
                <el-form-item label="邮箱" prop="email">
                  <el-input v-model="registerForm.email" placeholder="可选，如 alice@example.com" />
                </el-form-item>
                <el-form-item label="昵称" prop="nickname">
                  <el-input v-model="registerForm.nickname" placeholder="可选" />
                </el-form-item>
                <el-button type="primary" :loading="registering" @click="onRegister">
                  创建账号
                </el-button>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="tip-card">
          <h3>联调提示</h3>
          <ul>
            <li>登录成功后，前端会自动保存 JWT 并注入到受保护接口。</li>
            <li>实时视频 WebSocket 会自动拼接 `?token=&lt;jwt&gt;`。</li>
            <li>若接口返回 `401`，前端会自动清理会话并跳回登录页。</li>
            <li>默认管理员账号：`admin / Admin@123456`。</li>
          </ul>
        </el-card>
      </el-col>
    </el-row>
  </PageContainer>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { type FormInstance, type FormRules, ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import PageContainer from '../components/PageContainer.vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref<'login' | 'register'>('login')
const registering = ref(false)
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

const loginForm = reactive({
  username: 'admin',
  password: 'Admin@123456',
})

const registerForm = reactive({
  username: '',
  password: '',
  email: '',
  nickname: '',
})

const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 32, message: '用户名长度需在 3-32 位之间', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 128, message: '密码长度需在 8-128 位之间', trigger: 'blur' },
  ],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
}

const resolveRedirectPath = () => {
  const redirect = route.query.redirect
  if (typeof redirect === 'string' && redirect.startsWith('/')) {
    return redirect
  }
  return authStore.isAdmin ? '/admin' : '/segment'
}

const onLogin = async () => {
  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  try {
    await authStore.login({
      username: loginForm.username.trim(),
      password: loginForm.password,
    })
    ElMessage.success('登录成功')
    await router.push(resolveRedirectPath())
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '登录失败')
  }
}

const onRegister = async () => {
  const valid = await registerFormRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  registering.value = true
  try {
    await authStore.register({
      username: registerForm.username.trim(),
      password: registerForm.password,
      email: registerForm.email.trim() || undefined,
      nickname: registerForm.nickname.trim() || undefined,
    })
    ElMessage.success('注册成功，请使用新账号登录')
    activeTab.value = 'login'
    loginForm.username = registerForm.username.trim()
    loginForm.password = registerForm.password
    registerFormRef.value?.resetFields()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '注册失败')
  } finally {
    registering.value = false
  }
}
</script>

<style scoped>
.auth-row {
  margin-top: 8px;
}

.auth-card,
.tip-card {
  height: 100%;
}

.tip-card h3 {
  margin: 0 0 10px;
  color: #1e3047;
}

.tip-card ul {
  margin: 0;
  padding-left: 20px;
  color: #415771;
  line-height: 1.8;
}
</style>
