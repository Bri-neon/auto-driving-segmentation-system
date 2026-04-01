import { defineStore } from 'pinia'

import {
  deleteAdminHistory,
  fetchAdminHistories,
  fetchAdminHistoryDetail,
  fetchAdminUsers,
  resetAdminUserPassword,
  updateAdminHistory,
  updateAdminUser,
  type AdminHistoryListQuery,
  type AdminHistoryUpdatePayload,
  type AdminUserItem,
  type AdminUserUpdatePayload,
  type HistoryItem,
  type HistoryProcessMode,
  type HistoryRequestType,
} from '../api'

interface AdminState {
  users: AdminUserItem[]
  usersTotal: number
  usersPage: number
  usersPageSize: number
  userKeyword: string
  userRole: 'admin' | 'user' | null
  userActive: boolean | null
  usersLoading: boolean

  histories: HistoryItem[]
  historiesTotal: number
  historiesPage: number
  historiesPageSize: number
  historyUserId: number | null
  historyUsername: string
  historyRequestType: HistoryRequestType | null
  historyProcessMode: HistoryProcessMode | null
  historiesLoading: boolean
}

export const useAdminStore = defineStore('admin', {
  state: (): AdminState => ({
    users: [],
    usersTotal: 0,
    usersPage: 1,
    usersPageSize: 20,
    userKeyword: '',
    userRole: null,
    userActive: null,
    usersLoading: false,

    histories: [],
    historiesTotal: 0,
    historiesPage: 1,
    historiesPageSize: 20,
    historyUserId: null,
    historyUsername: '',
    historyRequestType: null,
    historyProcessMode: null,
    historiesLoading: false,
  }),
  actions: {
    async loadUsers(page?: number) {
      const targetPage = page ?? this.usersPage
      this.usersLoading = true
      try {
        const data = await fetchAdminUsers({
          page: targetPage,
          page_size: this.usersPageSize,
          keyword: this.userKeyword.trim() || undefined,
          role: this.userRole || undefined,
          is_active: this.userActive === null ? undefined : this.userActive,
        })
        this.users = data.items
        this.usersTotal = data.total
        this.usersPage = data.page
        this.usersPageSize = data.page_size
      } finally {
        this.usersLoading = false
      }
    },

    async reloadUsersWithFilters() {
      this.usersPage = 1
      await this.loadUsers(1)
    },

    async patchUser(userId: number, payload: AdminUserUpdatePayload) {
      const data = await updateAdminUser(userId, payload)
      const index = this.users.findIndex((item) => item.id === userId)
      if (index >= 0) {
        this.users[index] = data.user
      }
      return data.user
    },

    async resetPassword(userId: number, newPassword: string) {
      return resetAdminUserPassword(userId, { new_password: newPassword })
    },

    async loadHistories(page?: number) {
      const targetPage = page ?? this.historiesPage
      this.historiesLoading = true
      try {
        const params: AdminHistoryListQuery = {
          page: targetPage,
          page_size: this.historiesPageSize,
          request_type: this.historyRequestType || undefined,
          process_mode: this.historyProcessMode || undefined,
          user_id: this.historyUserId || undefined,
          username: this.historyUsername.trim() || undefined,
        }
        const data = await fetchAdminHistories(params)
        this.histories = data.items
        this.historiesTotal = data.total
        this.historiesPage = data.page
        this.historiesPageSize = data.page_size
      } finally {
        this.historiesLoading = false
      }
    },

    async reloadHistoriesWithFilters() {
      this.historiesPage = 1
      await this.loadHistories(1)
    },

    async getHistoryDetail(historyId: number) {
      const data = await fetchAdminHistoryDetail(historyId)
      return data.item
    },

    async patchHistory(historyId: number, payload: AdminHistoryUpdatePayload) {
      const data = await updateAdminHistory(historyId, payload)
      const updated = data.item
      const index = this.histories.findIndex((item) => item.id === historyId)
      if (index >= 0) {
        this.histories[index] = updated
      }
      return updated
    },

    async removeHistory(historyId: number) {
      await deleteAdminHistory(historyId)
      this.histories = this.histories.filter((item) => item.id !== historyId)
      this.historiesTotal = Math.max(0, this.historiesTotal - 1)
      if (this.histories.length === 0 && this.historiesTotal > 0 && this.historiesPage > 1) {
        await this.loadHistories(this.historiesPage - 1)
      }
    },
  },
})
