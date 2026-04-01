<template>
  <PageContainer
    title="管理后台"
    description="管理员可在此管理用户与全站推理历史，支持审核与风险内容处理。"
  >
    <el-alert
      title="仅管理员可访问。你可以修改用户资料、重置密码、处理违规历史记录。"
      type="warning"
      :closable="false"
      show-icon
    />

    <el-tabs v-model="activeTab" class="admin-tabs">
      <el-tab-pane label="用户管理" name="users">
        <el-card shadow="never" class="filter-card">
          <el-row :gutter="12">
            <el-col :xs="24" :md="8" :lg="6">
              <el-input v-model="adminStore.userKeyword" placeholder="用户名/邮箱/昵称关键字" clearable />
            </el-col>
            <el-col :xs="24" :md="8" :lg="4">
              <el-select v-model="adminStore.userRole" placeholder="角色" clearable>
                <el-option label="管理员" value="admin" />
                <el-option label="普通用户" value="user" />
              </el-select>
            </el-col>
            <el-col :xs="24" :md="8" :lg="4">
              <el-select v-model="userActiveModel" placeholder="状态" clearable>
                <el-option label="启用" :value="true" />
                <el-option label="禁用" :value="false" />
              </el-select>
            </el-col>
            <el-col :xs="24" :md="24" :lg="6">
              <el-button type="primary" :loading="adminStore.usersLoading" @click="onUserFilter">查询用户</el-button>
            </el-col>
          </el-row>
        </el-card>

        <el-card shadow="never" class="table-card">
          <el-table :data="adminStore.users" v-loading="adminStore.usersLoading" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="username" label="用户名" min-width="120" />
            <el-table-column prop="nickname" label="昵称" min-width="110" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
            <el-table-column prop="role" label="角色" width="90">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">{{ row.role }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'warning'" size="small">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" min-width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="last_login_at" label="最后登录" min-width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.last_login_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" fixed="right" width="190">
              <template #default="{ row }">
                <el-space>
                  <el-button size="small" @click="openUserEdit(row)">编辑</el-button>
                  <el-button size="small" type="warning" plain @click="openResetPassword(row.id)">重置密码</el-button>
                </el-space>
              </template>
            </el-table-column>
          </el-table>

          <div class="pager-wrap">
            <el-pagination
              background
              layout="total, sizes, prev, pager, next, jumper"
              :total="adminStore.usersTotal"
              :current-page="adminStore.usersPage"
              :page-size="adminStore.usersPageSize"
              :page-sizes="[10, 20, 50, 100]"
              @current-change="onUserPageChange"
              @size-change="onUserPageSizeChange"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="历史管理" name="histories">
        <el-card shadow="never" class="filter-card">
          <el-row :gutter="12">
            <el-col :xs="24" :md="8" :lg="5">
              <el-input v-model="adminStore.historyUsername" placeholder="用户名关键字" clearable />
            </el-col>
            <el-col :xs="24" :md="8" :lg="4">
              <el-input-number v-model="adminStore.historyUserId" :min="1" :precision="0" style="width: 100%" />
            </el-col>
            <el-col :xs="24" :md="8" :lg="4">
              <el-select v-model="adminStore.historyRequestType" placeholder="请求类型" clearable>
                <el-option label="图像" value="image" />
                <el-option label="视频" value="video" />
              </el-select>
            </el-col>
            <el-col :xs="24" :md="8" :lg="4">
              <el-select v-model="adminStore.historyProcessMode" placeholder="处理模式" clearable>
                <el-option label="同步" value="sync" />
                <el-option label="实时" value="realtime" />
              </el-select>
            </el-col>
            <el-col :xs="24" :md="8" :lg="4">
              <el-button type="primary" :loading="adminStore.historiesLoading" @click="onHistoryFilter">查询历史</el-button>
            </el-col>
          </el-row>
          <p class="filter-tip">用户 ID 不筛选时请置空（当前可删除该值）。</p>
        </el-card>

        <el-card shadow="never" class="table-card">
          <el-table :data="adminStore.histories" v-loading="adminStore.historiesLoading" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column label="用户" min-width="140">
              <template #default="{ row }">
                <div class="user-cell">
                  <strong>{{ row.user_username || '-' }}</strong>
                  <span>ID: {{ row.user_id || '-' }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="request_type" label="类型" width="80" />
            <el-table-column prop="process_mode" label="模式" width="90" />
            <el-table-column prop="model_name" label="模型" min-width="140" />
            <el-table-column prop="status_message" label="状态信息" min-width="180" />
            <el-table-column prop="created_at" label="创建时间" min-width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" fixed="right" width="170">
              <template #default="{ row }">
                <el-space>
                  <el-button size="small" @click="openHistoryEdit(row.id)">编辑</el-button>
                  <el-button size="small" type="danger" plain @click="onDeleteHistory(row.id)">删除</el-button>
                </el-space>
              </template>
            </el-table-column>
          </el-table>

          <div class="pager-wrap">
            <el-pagination
              background
              layout="total, sizes, prev, pager, next, jumper"
              :total="adminStore.historiesTotal"
              :current-page="adminStore.historiesPage"
              :page-size="adminStore.historiesPageSize"
              :page-sizes="[10, 20, 50, 100]"
              @current-change="onHistoryPageChange"
              @size-change="onHistoryPageSizeChange"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="userEditVisible" title="编辑用户" width="520px">
      <el-form :model="userEditForm" label-position="top">
        <el-form-item label="邮箱">
          <el-input v-model="userEditForm.email" placeholder="可留空" />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="userEditForm.nickname" placeholder="可留空" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userEditForm.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="userEditForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userEditVisible = false">取消</el-button>
        <el-button type="primary" :loading="userSubmitting" @click="submitUserEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resetPwdVisible" title="重置用户密码" width="460px">
      <el-form :model="resetPwdForm" label-position="top">
        <el-form-item label="新密码（至少 8 位）">
          <el-input v-model="resetPwdForm.newPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdVisible = false">取消</el-button>
        <el-button type="warning" :loading="resetSubmitting" @click="submitResetPassword">确认重置</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="historyEditVisible" title="编辑历史记录" width="620px">
      <el-form :model="historyEditForm" label-position="top">
        <el-form-item label="实时状态">
          <el-input v-model="historyEditForm.realtime_status" />
        </el-form-item>
        <el-form-item label="最终状态">
          <el-input v-model="historyEditForm.finalize_status" />
        </el-form-item>
        <el-form-item label="状态信息">
          <el-input v-model="historyEditForm.status_message" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="分割结果 URL">
          <el-input v-model="historyEditForm.segmented_url" />
        </el-form-item>
        <el-form-item label="融合结果 URL">
          <el-input v-model="historyEditForm.overlay_url" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="historyEditVisible = false">取消</el-button>
        <el-button type="primary" :loading="historySubmitting" @click="submitHistoryEdit">保存</el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageContainer from '../components/PageContainer.vue'
import { type AdminUserItem } from '../api'
import { useAdminStore } from '../stores/admin'
import { formatDateTime } from '../utils/format'

const adminStore = useAdminStore()
const activeTab = ref<'users' | 'histories'>('users')

const userActiveModel = computed({
  get: () => adminStore.userActive,
  set: (value: boolean | null) => {
    adminStore.userActive = value
  },
})

const userEditVisible = ref(false)
const userSubmitting = ref(false)
const editingUserId = ref<number | null>(null)
const userEditForm = reactive({
  email: '',
  nickname: '',
  role: 'user' as 'admin' | 'user',
  is_active: true,
})

const resetPwdVisible = ref(false)
const resetSubmitting = ref(false)
const resetPwdUserId = ref<number | null>(null)
const resetPwdForm = reactive({
  newPassword: '',
})

const historyEditVisible = ref(false)
const historySubmitting = ref(false)
const editingHistoryId = ref<number | null>(null)
const historyEditForm = reactive({
  realtime_status: '',
  finalize_status: '',
  status_message: '',
  segmented_url: '',
  overlay_url: '',
})

const onUserFilter = async () => {
  try {
    await adminStore.reloadUsersWithFilters()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '查询用户失败')
  }
}

const onUserPageChange = async (page: number) => {
  try {
    await adminStore.loadUsers(page)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载用户失败')
  }
}

const onUserPageSizeChange = async (size: number) => {
  adminStore.usersPageSize = size
  try {
    await adminStore.loadUsers(1)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '更新分页失败')
  }
}

const openUserEdit = (user: AdminUserItem) => {
  editingUserId.value = user.id
  userEditForm.email = user.email || ''
  userEditForm.nickname = user.nickname || ''
  userEditForm.role = user.role === 'admin' ? 'admin' : 'user'
  userEditForm.is_active = user.is_active
  userEditVisible.value = true
}

const submitUserEdit = async () => {
  if (!editingUserId.value) return
  userSubmitting.value = true
  try {
    await adminStore.patchUser(editingUserId.value, {
      email: userEditForm.email.trim() || null,
      nickname: userEditForm.nickname.trim() || null,
      role: userEditForm.role,
      is_active: userEditForm.is_active,
    })
    ElMessage.success('用户信息更新成功')
    userEditVisible.value = false
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '更新用户失败')
  } finally {
    userSubmitting.value = false
  }
}

const openResetPassword = (userId: number) => {
  resetPwdUserId.value = userId
  resetPwdForm.newPassword = ''
  resetPwdVisible.value = true
}

const submitResetPassword = async () => {
  if (!resetPwdUserId.value) return
  if (resetPwdForm.newPassword.length < 8) {
    ElMessage.warning('新密码长度至少 8 位')
    return
  }
  resetSubmitting.value = true
  try {
    await adminStore.resetPassword(resetPwdUserId.value, resetPwdForm.newPassword)
    ElMessage.success('用户密码已重置')
    resetPwdVisible.value = false
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '重置密码失败')
  } finally {
    resetSubmitting.value = false
  }
}

const onHistoryFilter = async () => {
  try {
    await adminStore.reloadHistoriesWithFilters()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '查询历史失败')
  }
}

const onHistoryPageChange = async (page: number) => {
  try {
    await adminStore.loadHistories(page)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载历史失败')
  }
}

const onHistoryPageSizeChange = async (size: number) => {
  adminStore.historiesPageSize = size
  try {
    await adminStore.loadHistories(1)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '更新分页失败')
  }
}

const openHistoryEdit = async (historyId: number) => {
  try {
    const item = await adminStore.getHistoryDetail(historyId)
    editingHistoryId.value = historyId
    historyEditForm.realtime_status = item.realtime_status || ''
    historyEditForm.finalize_status = item.finalize_status || ''
    historyEditForm.status_message = item.status_message || ''
    historyEditForm.segmented_url = item.segmented_url || ''
    historyEditForm.overlay_url = item.overlay_url || ''
    historyEditVisible.value = true
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '获取历史详情失败')
  }
}

const submitHistoryEdit = async () => {
  if (!editingHistoryId.value) return
  historySubmitting.value = true
  try {
    await adminStore.patchHistory(editingHistoryId.value, {
      realtime_status: historyEditForm.realtime_status.trim() || null,
      finalize_status: historyEditForm.finalize_status.trim() || null,
      status_message: historyEditForm.status_message.trim() || null,
      segmented_url: historyEditForm.segmented_url.trim() || null,
      overlay_url: historyEditForm.overlay_url.trim() || null,
    })
    ElMessage.success('历史记录更新成功')
    historyEditVisible.value = false
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '更新历史失败')
  } finally {
    historySubmitting.value = false
  }
}

const onDeleteHistory = async (historyId: number) => {
  try {
    await ElMessageBox.confirm('删除后将无法恢复，确认删除该历史记录？', '删除确认', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await adminStore.removeHistory(historyId)
    ElMessage.success('历史记录已删除')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '删除历史失败')
  }
}

onMounted(async () => {
  await Promise.all([adminStore.loadUsers(), adminStore.loadHistories()]).catch((error) => {
    ElMessage.error(error instanceof Error ? error.message : '初始化管理后台失败')
  })
})
</script>

<style scoped>
.admin-tabs {
  margin-top: 8px;
}

.filter-card,
.table-card {
  margin-top: 8px;
}

.filter-card :deep(.el-select),
.filter-card :deep(.el-input-number) {
  width: 100%;
}

.filter-tip {
  margin: 8px 0 0;
  font-size: 12px;
  color: #5f728a;
}

.pager-wrap {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.user-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-cell strong {
  color: #253a54;
}

.user-cell span {
  color: #667a92;
  font-size: 12px;
}
</style>
