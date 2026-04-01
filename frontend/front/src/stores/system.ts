import { defineStore } from 'pinia'

import { fetchModelInfo, modelOptions, type ModelInfo, type ModelKey, type ModelOption } from '../api'

interface SystemState {
  title: string
  subtitle: string
  modelOptions: ModelOption[]
  selectedModelKey: ModelKey
  modelInfo: ModelInfo | null
  modelLoading: boolean
}

export const useSystemStore = defineStore('system', {
  state: (): SystemState => ({
    title: '自动驾驶图像语义分割系统',
    subtitle: '基于卷积神经网络的自动驾驶场景图像语义分割',
    modelOptions,
    selectedModelKey: 'bisenetv2',
    modelInfo: null,
    modelLoading: false,
  }),
  actions: {
    async loadModelInfo() {
      this.modelLoading = true
      try {
        this.modelInfo = await fetchModelInfo(this.selectedModelKey)
      } finally {
        this.modelLoading = false
      }
    },

    async setModelKey(modelKey: ModelKey) {
      if (this.selectedModelKey === modelKey) {
        return
      }
      this.selectedModelKey = modelKey
      await this.loadModelInfo()
    },
  },
})
