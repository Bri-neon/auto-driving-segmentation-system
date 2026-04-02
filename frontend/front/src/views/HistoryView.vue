<template>
  <PageContainer
    title="推理历史"
    description="展示当前登录用户的图像/视频推理记录，支持筛选、分页、详情查看和删除。"
  >
    <el-card shadow="never" class="filter-card">
      <el-row :gutter="12" class="filter-row">
        <el-col :xs="24" :md="8" :lg="6">
          <el-select v-model="requestTypeModel" placeholder="请求类型" clearable @change="onFilterChange">
            <el-option label="图像" value="image" />
            <el-option label="视频" value="video" />
          </el-select>
        </el-col>
        <el-col :xs="24" :md="8" :lg="6">
          <el-select v-model="processModeModel" placeholder="处理模式" clearable @change="onFilterChange">
            <el-option label="同步" value="sync" />
            <el-option label="实时" value="realtime" />
          </el-select>
        </el-col>
        <el-col :xs="24" :md="8" :lg="6">
          <el-button :loading="historyStore.loading" class="ripple-btn" @click="onRefresh">刷新列表</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="table-card">
      <el-table :data="historyStore.items" v-loading="historyStore.loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="created_at" label="创建时间" min-width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="request_type" label="请求类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.request_type === 'image' ? 'success' : 'warning'">
              {{ row.request_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="process_mode" label="处理模式" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.process_mode === 'sync' ? 'info' : 'primary'">
              {{ row.process_mode }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型" min-width="170" />
        <el-table-column prop="resolution" label="分辨率" width="95" />
        <el-table-column label="阶段状态" min-width="180">
          <template #default="{ row }">
            <div class="status-cell">
              <span>RT: {{ row.realtime_status }}</span>
              <span>FZ: {{ row.finalize_status }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="媒体" width="80">
          <template #default="{ row }">
            <el-link :href="resolveMediaUrl(row)" target="_blank" type="primary">查看</el-link>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="160">
          <template #default="{ row }">
            <el-space>
              <el-button size="small" class="ripple-btn" @click="openDetail(row.id)">详情</el-button>
              <el-button
                size="small"
                type="danger"
                plain
                :loading="historyStore.deletingIds.includes(row.id)"
                class="ripple-btn"
                @click="onDelete(row.id)"
              >
                删除
              </el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager-wrap">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :total="historyStore.total"
          :current-page="historyStore.page"
          :page-size="historyStore.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          @current-change="onPageChange"
          @size-change="onPageSizeChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" width="860px" title="历史详情">
      <el-skeleton :loading="detailLoading" animated :rows="6">
        <template #default>
          <template v-if="detailItem">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="记录 ID">{{ detailItem.id }}</el-descriptions-item>
              <el-descriptions-item label="任务 ID">{{ detailItem.task_id || '-' }}</el-descriptions-item>
              <el-descriptions-item label="请求类型">{{ detailItem.request_type }}</el-descriptions-item>
              <el-descriptions-item label="处理模式">{{ detailItem.process_mode }}</el-descriptions-item>
              <el-descriptions-item label="模型">{{ detailItem.model_name }}</el-descriptions-item>
              <el-descriptions-item label="分辨率">{{ detailItem.resolution || '-' }}</el-descriptions-item>
              <el-descriptions-item label="实时状态">{{ detailItem.realtime_status }}</el-descriptions-item>
              <el-descriptions-item label="最终状态">{{ detailItem.finalize_status }}</el-descriptions-item>
              <el-descriptions-item label="推理耗时">
                {{ detailItem.inference_time ? formatMs(detailItem.inference_time) : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="实时 FPS">
                {{ detailItem.realtime_fps ?? '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="平均 FPS">
                {{ detailItem.avg_fps ?? '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="更新时间">
                {{ formatDateTime(detailItem.updated_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="状态信息" :span="2">
                {{ detailItem.status_message || '-' }}
              </el-descriptions-item>
            </el-descriptions>

            <el-row :gutter="12" class="preview-row">
              <el-col :xs="24" :md="8">
                <el-card shadow="never" class="preview-card">
                  <template #header>原始媒体</template>
                  <template v-if="isImageDetail">
                    <el-image
                      v-if="originalMediaUrl"
                      :src="originalMediaUrl"
                      fit="contain"
                      class="preview-image"
                      :preview-src-list="[originalMediaUrl]"
                    />
                    <el-empty v-else description="暂无数据" :image-size="60" />
                  </template>
                  <template v-else>
                    <video v-if="originalMediaUrl" :src="originalMediaUrl" controls preload="metadata" class="preview-video" />
                    <el-empty v-else description="暂无数据" :image-size="60" />
                  </template>
                </el-card>
              </el-col>

              <el-col :xs="24" :md="8">
                <el-card shadow="never" class="preview-card">
                  <template #header>分割结果</template>
                  <template v-if="isImageDetail">
                    <el-image
                      v-if="segmentedMediaUrl"
                      :src="segmentedMediaUrl"
                      fit="contain"
                      class="preview-image"
                      :preview-src-list="[segmentedMediaUrl]"
                    />
                    <el-empty v-else description="暂无数据" :image-size="60" />
                  </template>
                  <template v-else>
                    <video
                      v-if="segmentedMediaUrl"
                      :src="segmentedMediaUrl"
                      controls
                      preload="metadata"
                      class="preview-video"
                    />
                    <el-empty v-else description="暂无数据" :image-size="60" />
                  </template>
                </el-card>
              </el-col>

              <el-col :xs="24" :md="8">
                <el-card shadow="never" class="preview-card">
                  <template #header>融合结果</template>
                  <template v-if="isImageDetail">
                    <el-image
                      v-if="overlayMediaUrl"
                      :src="overlayMediaUrl"
                      fit="contain"
                      class="preview-image"
                      :preview-src-list="[overlayMediaUrl]"
                    />
                    <el-empty v-else description="暂无数据" :image-size="60" />
                  </template>
                  <template v-else>
                    <video v-if="overlayMediaUrl" :src="overlayMediaUrl" controls preload="metadata" class="preview-video" />
                    <el-empty v-else description="暂无数据" :image-size="60" />
                  </template>
                </el-card>
              </el-col>
            </el-row>
          </template>
        </template>
      </el-skeleton>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageContainer from '../components/PageContainer.vue'
import { type HistoryItem, type HistoryProcessMode, type HistoryRequestType } from '../api'
import { useHistoryStore } from '../stores/history'
import { formatDateTime, formatMs, resolveAssetUrl } from '../utils/format'

const historyStore = useHistoryStore()
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailItem = ref<HistoryItem | null>(null)

const requestTypeModel = computed({
  get: () => historyStore.requestType,
  set: (value: HistoryRequestType | null) => {
    historyStore.setRequestType(value)
  },
})

const processModeModel = computed({
  get: () => historyStore.processMode,
  set: (value: HistoryProcessMode | null) => {
    historyStore.setProcessMode(value)
  },
})

const isImageDetail = computed(() => detailItem.value?.request_type === 'image')
const originalMediaUrl = computed(() => resolveAssetUrl(detailItem.value?.original_url || ''))
const segmentedMediaUrl = computed(() => resolveAssetUrl(detailItem.value?.segmented_url || ''))
const overlayMediaUrl = computed(() => resolveAssetUrl(detailItem.value?.overlay_url || ''))

const resolveMediaUrl = (row: HistoryItem) => {
  return resolveAssetUrl(row.overlay_url || row.segmented_url || row.original_url)
}

const onFilterChange = async () => {
  try {
    await historyStore.reloadWithFilters()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '筛选失败')
  }
}

const onRefresh = async () => {
  try {
    await historyStore.loadHistories(historyStore.page)
    ElMessage.success('历史记录已刷新')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '刷新失败')
  }
}

const onPageChange = async (page: number) => {
  try {
    await historyStore.loadHistories(page)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '分页加载失败')
  }
}

const onPageSizeChange = async (pageSize: number) => {
  historyStore.setPageSize(pageSize)
  try {
    await historyStore.loadHistories(1)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '分页大小更新失败')
  }
}

const openDetail = async (historyId: number) => {
  detailVisible.value = true
  detailLoading.value = true
  try {
    detailItem.value = await historyStore.getHistoryDetail(historyId)
  } catch (error) {
    detailVisible.value = false
    ElMessage.error(error instanceof Error ? error.message : '获取历史详情失败')
  } finally {
    detailLoading.value = false
  }
}

const onDelete = async (historyId: number) => {
  try {
    await ElMessageBox.confirm('删除后将无法恢复，确认继续吗？', '删除确认', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await historyStore.deleteHistoryItem(historyId)
    ElMessage.success('删除成功')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '删除失败')
  }
}

onMounted(async () => {
  try {
    await historyStore.loadHistories()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '历史记录加载失败')
  }
})
</script>

<style scoped>
.filter-card,
.table-card {
  margin-top: 8px;
}

.filter-row :deep(.el-select) {
  width: 100%;
}

.status-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: #51657d;
  font-size: 12px;
}

.pager-wrap {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.preview-row {
  margin-top: 14px;
}

.preview-card {
  min-height: 280px;
}

.preview-image,
.preview-video {
  width: 100%;
  height: 210px;
  border-radius: 6px;
  background: #f6f8fc;
}

.preview-video {
  background: #111c2d;
}
</style>
