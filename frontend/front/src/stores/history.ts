import { defineStore } from 'pinia'

import {
  deleteHistory as deleteHistoryApi,
  fetchHistoryDetail as fetchHistoryDetailApi,
  fetchHistoryList,
  type HistoryItem,
  type HistoryProcessMode,
  type HistoryRequestType,
} from '../api'

type NullableHistoryRequestType = HistoryRequestType | null
type NullableHistoryProcessMode = HistoryProcessMode | null

interface HistoryState {
  items: HistoryItem[]
  total: number
  page: number
  pageSize: number
  requestType: NullableHistoryRequestType
  processMode: NullableHistoryProcessMode
  loading: boolean
  deletingIds: number[]
}

export const useHistoryStore = defineStore('history', {
  state: (): HistoryState => ({
    items: [],
    total: 0,
    page: 1,
    pageSize: 20,
    requestType: null,
    processMode: null,
    loading: false,
    deletingIds: [],
  }),
  actions: {
    async loadHistories(page?: number) {
      const targetPage = page ?? this.page
      this.loading = true
      try {
        const data = await fetchHistoryList({
          page: targetPage,
          page_size: this.pageSize,
          request_type: this.requestType || undefined,
          process_mode: this.processMode || undefined,
        })

        this.total = data.total
        this.page = data.page
        this.pageSize = data.page_size
        this.items = data.items
      } finally {
        this.loading = false
      }
    },

    setRequestType(requestType: NullableHistoryRequestType) {
      this.requestType = requestType
    },

    setProcessMode(processMode: NullableHistoryProcessMode) {
      this.processMode = processMode
    },

    setPageSize(pageSize: number) {
      this.pageSize = pageSize
    },

    async reloadWithFilters() {
      this.page = 1
      await this.loadHistories(1)
    },

    async deleteHistoryItem(historyId: number) {
      if (this.deletingIds.includes(historyId)) {
        return
      }

      this.deletingIds.push(historyId)
      try {
        await deleteHistoryApi(historyId)
        this.items = this.items.filter((item) => item.id !== historyId)
        this.total = Math.max(0, this.total - 1)

        if (this.items.length === 0 && this.total > 0 && this.page > 1) {
          await this.loadHistories(this.page - 1)
        }
      } finally {
        this.deletingIds = this.deletingIds.filter((id) => id !== historyId)
      }
    },

    async getHistoryDetail(historyId: number) {
      const data = await fetchHistoryDetailApi(historyId)
      return data.item
    },
  },
})
