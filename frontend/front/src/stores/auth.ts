import { defineStore } from 'pinia'

import {
  changeMyPassword,
  fetchCurrentUser,
  loginUser,
  registerUser,
  updateMyProfile,
  uploadAvatar as uploadAvatarApi,
  type AuthLoginData,
  type AuthLoginPayload,
  type AuthRegisterData,
  type AuthRegisterPayload,
  type PasswordChangePayload,
  type ProfileUpdatePayload,
  type UserProfile,
} from '../api'
import { clearAuthStorage, getAccessExpiresAt, getAccessToken, getAccessTokenRole, setAuthSession } from '../utils/auth'

interface AuthState {
  accessToken: string
  accessExpiresAt: number | null
  user: UserProfile | null
  loading: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    accessToken: getAccessToken(),
    accessExpiresAt: getAccessExpiresAt(),
    user: null,
    loading: false,
  }),
  getters: {
    isAuthenticated: (state) => {
      if (!state.accessToken) {
        return false
      }
      if (!state.accessExpiresAt) {
        return true
      }
      return state.accessExpiresAt > Date.now()
    },
    displayName: (state) => state.user?.nickname || state.user?.username || '',
    isAdmin: (state) => {
      const role = state.user?.role || getAccessTokenRole()
      return role === 'admin'
    },
  },
  actions: {
    syncSessionFromStorage() {
      this.accessToken = getAccessToken()
      this.accessExpiresAt = getAccessExpiresAt()
    },

    applyLoginSession(payload: AuthLoginData) {
      setAuthSession(payload.access_token, payload.expires_in)
      this.syncSessionFromStorage()
      this.user = payload.user
    },

    async register(payload: AuthRegisterPayload): Promise<AuthRegisterData> {
      return registerUser(payload)
    },

    async login(payload: AuthLoginPayload): Promise<AuthLoginData> {
      this.loading = true
      try {
        const data = await loginUser(payload)
        this.applyLoginSession(data)
        return data
      } finally {
        this.loading = false
      }
    },

    async refreshCurrentUser() {
      if (!this.accessToken) {
        this.user = null
        return null
      }

      this.loading = true
      try {
        const data = await fetchCurrentUser()
        this.user = data.user
        return data.user
      } finally {
        this.loading = false
      }
    },

    async updateProfile(payload: ProfileUpdatePayload) {
      const data = await updateMyProfile(payload)
      this.user = data.user
      return data
    },

    async changePassword(payload: PasswordChangePayload) {
      return changeMyPassword(payload)
    },

    async updateAvatar(file: File) {
      const data = await uploadAvatarApi(file)
      if (this.user) {
        this.user = {
          ...this.user,
          avatar_url: data.avatar_url,
        }
      }
      return data
    },

    logout() {
      clearAuthStorage()
      this.accessToken = ''
      this.accessExpiresAt = null
      this.user = null
    },
  },
})
