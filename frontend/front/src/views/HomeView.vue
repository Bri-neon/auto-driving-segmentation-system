<template>
  <PageContainer
    title="自动驾驶图像语义分割系统"
    description="基于卷积神经网络的自动驾驶场景语义分割。支持图像/视频上传、模型切换、推理结果与 FPS 可视化展示。"
  >
    <el-row :gutter="16" class="home-row">
      <el-col :xs="24" :md="14">
        <el-card shadow="never" class="intro-card">
          <h3>项目背景</h3>
          <p>
            本系统服务于毕业设计《基于卷积神经网络的自动驾驶图像语义分割系统设计与实现》，
            重点展示图像级与视频级语义分割在道路场景理解中的可视化效果与工程化联调流程。
          </p>

          <h3>功能概览</h3>
          <ul>
            <li>上传自动驾驶场景图片并发起分割推理</li>
            <li>上传道路场景视频并展示实时 FPS 与分割可视化</li>
            <li>支持切换 DeepLabV3+ ResNet50 与 BiSeNetV2</li>
            <li>已接入登录鉴权与用户隔离的推理历史记录</li>
          </ul>

          <el-button type="primary" @click="goSegment">进入图像分割页面</el-button>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card shadow="never" class="cover-card">
          <img :src="heroImage" alt="系统示意图" />
          <p>系统示意图占位（可替换为模型流程图或实验结果图）</p>
        </el-card>
      </el-col>
    </el-row>
  </PageContainer>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

import heroImage from '../assets/hero.png'
import PageContainer from '../components/PageContainer.vue'

const router = useRouter()

const goSegment = () => {
  router.push('/segment')
}
</script>

<style scoped>
.home-row {
  margin-top: 8px;
}

.intro-card,
.cover-card {
  height: 100%;
}

.intro-card h3 {
  margin-top: 0;
  margin-bottom: 8px;
  color: #1f314a;
}

.intro-card p {
  margin-top: 0;
  margin-bottom: 16px;
  color: #5e6f84;
  line-height: 1.7;
}

.intro-card ul {
  margin: 0 0 20px;
  padding-left: 20px;
  color: #334861;
  line-height: 1.8;
}

.cover-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cover-card img {
  width: 100%;
  border-radius: 8px;
  border: 1px solid #d9e0ea;
  background: #f4f7fc;
}

.cover-card p {
  margin: 0;
  color: #6a7c93;
  font-size: 13px;
}
</style>
