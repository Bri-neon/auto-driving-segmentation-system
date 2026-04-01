<template>
  <PageContainer
    title="关于系统"
    description="用于毕业设计答辩展示的系统与模型说明页面。"
  >
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="about-card">
          <template #header>项目简介</template>
          <p>
            本项目聚焦自动驾驶场景语义分割任务，目标是对道路图像/视频进行像素级分类，
            为车辆环境感知与路径规划提供更精细的语义信息支撑。
          </p>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="about-card">
          <template #header>模型简介</template>
          <p>
            演示版本支持 DeepLabV3+ ResNet50 与 BiSeNetV2 两个模型切换，
            推理引擎可采用 ONNX Runtime，兼容 GPU 与 CPU 部署。
          </p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="about-card">
          <template #header>技术栈</template>
          <ul>
            <li>前端：Vue 3 + Vite + TypeScript</li>
            <li>路由：Vue Router</li>
            <li>状态管理：Pinia</li>
            <li>请求封装：Axios</li>
            <li>界面组件：Element Plus</li>
          </ul>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="about-card">
          <template #header>后端与联调说明</template>
          <p>
            后端已基于 FastAPI 完成登录鉴权、分割推理与历史记录落库。前端当前已接入
            `/api/auth/*`、`/api/history/*`、`/api/segment/*` 全链路接口，并支持 JWT 过期自动回登录页。
          </p>
        </el-card>
      </el-col>
    </el-row>
  </PageContainer>
</template>

<script setup lang="ts">
import PageContainer from '../components/PageContainer.vue'
</script>

<style scoped>
.about-card {
  height: 100%;
}

.about-card p {
  margin: 0;
  color: #4f627c;
  line-height: 1.8;
}

.about-card ul {
  margin: 0;
  padding-left: 20px;
  color: #334861;
  line-height: 1.9;
}

:deep(.el-row + .el-row) {
  margin-top: 16px;
}
</style>
