import axios, { AxiosError } from 'axios'

import type { ApiResponse } from './types'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/',
  timeout: 15000,
})

request.interceptors.response.use(
  (response) => {
    const payload = response.data as ApiResponse<unknown>

    if (typeof payload?.code === 'number' && payload.code !== 0) {
      return Promise.reject(new Error(payload.message || '接口返回异常'))
    }

    return response
  },
  (error: AxiosError<{ message?: string }>) => {
    const message = error.response?.data?.message || error.message || '网络请求失败'
    return Promise.reject(new Error(message))
  },
)

export default request
