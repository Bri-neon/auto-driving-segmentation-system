import axios, { AxiosError, AxiosHeaders } from 'axios'

import type { ApiResponse } from './types'
import { AUTH_UNAUTHORIZED_EVENT, clearAuthStorage, getAccessToken } from '../utils/auth'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/',
  timeout: 15000,
})

request.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (!token) {
    return config
  }

  const headers = AxiosHeaders.from(config.headers)
  if (!headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  config.headers = headers

  return config
})

request.interceptors.response.use(
  (response) => {
    const payload = response.data as ApiResponse<unknown>

    if (typeof payload?.code === 'number' && payload.code !== 0) {
      return Promise.reject(new Error(payload.message || '接口返回异常'))
    }

    return response
  },
  (error: AxiosError<ApiResponse<unknown>>) => {
    if (error.response?.status === 401) {
      clearAuthStorage()
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event(AUTH_UNAUTHORIZED_EVENT))
      }
    }

    const message = error.response?.data?.message || error.message || '网络请求失败'
    return Promise.reject(new Error(message))
  },
)

export default request
